import re

import requests
from requests.auth import HTTPBasicAuth


def _pick_config_value(config, *keys):
    if not isinstance(config, dict):
        return ""
    for key in keys:
        value = config.get(key)
        if value not in (None, ""):
            return value
    return ""


def fetch_ticket(ticket_key, config):
    if not ticket_key or not re.search(r'\b[A-Z]+-\d+\b', ticket_key):
        raise ValueError('Invalid Jira ticket key.')

    jira_url = _pick_config_value(config, 'jira_base_url', 'jira_url', 'jira_base')
    jira_email = _pick_config_value(config, 'jira_email', 'jira_user', 'jira_username')
    jira_api_token = _pick_config_value(config, 'jira_api_token', 'jira_token')

    if not jira_url:
        raise ValueError('Jira configuration is missing.')
    if not jira_email or not jira_api_token:
        raise ValueError('Jira credentials are missing.')

    endpoint = f"{jira_url.rstrip('/')}/rest/api/3/issue/{ticket_key}"
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(jira_email, jira_api_token),
            timeout=15,
        )
    except requests.exceptions.Timeout as exc:
        raise TimeoutError('Jira is unavailable or timed out.') from exc
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError('Jira is unavailable.') from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError('Jira is unavailable.') from exc

    if response.status_code == 401 or response.status_code == 403:
        raise PermissionError('Jira authentication failed.')
    if response.status_code == 404:
        raise FileNotFoundError(f'Ticket {ticket_key} was not found.')
    if response.status_code >= 500:
        raise RuntimeError('Jira is unavailable.')
    if response.status_code != 200:
        raise RuntimeError('Unexpected Jira response.')

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError('Unexpected Jira response.') from exc

    fields = payload.get('fields', {})
    summary = fields.get('summary', '') or 'Not specified'
    description = fields.get('description', '')
    if isinstance(description, list):
        description = '\n'.join(item.get('text', '') for item in description if isinstance(item, dict))
    elif description is None:
        description = ''
    description = str(description).strip() if description else ''

    if not description:
        raise ValueError('Jira description is empty.')

    acceptance_criteria = (
        fields.get('acceptance_criteria')
        or fields.get('acceptanceCriteria')
        or fields.get('customfield_10055')
        or 'Not specified'
    )
    if isinstance(acceptance_criteria, list):
        acceptance_criteria = '\n'.join(item.get('text', '') for item in acceptance_criteria if isinstance(item, dict))
    acceptance_criteria = str(acceptance_criteria).strip() if acceptance_criteria else 'Not specified'

    priority = fields.get('priority', {}).get('name', 'Not specified') if isinstance(fields.get('priority'), dict) else 'Not specified'
    issue_type = fields.get('issuetype', {}).get('name', 'Not specified') if isinstance(fields.get('issuetype'), dict) else 'Not specified'

    return {
        'summary': summary,
        'description': description,
        'acceptance_criteria': acceptance_criteria,
        'priority': priority,
        'issue_type': issue_type,
    }
