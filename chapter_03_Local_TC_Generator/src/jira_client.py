import requests
from requests.auth import HTTPBasicAuth
from config_store import read_config

def fetch_ticket(key: str):
    cfg = read_config()
    base = cfg.get("jira_base")
    user = cfg.get("jira_user")
    token = cfg.get("jira_token")
    if not base:
        raise RuntimeError("Jira base URL not configured")
    url = f"{base.rstrip('/')}/rest/api/2/issue/{key}"
    auth = None
    headers = {"Accept": "application/json"}
    if user and token:
        auth = HTTPBasicAuth(user, token)
    resp = requests.get(url, headers=headers, auth=auth, timeout=10)
    if resp.status_code == 404:
        raise ValueError(f"Ticket {key} not found (404)")
    resp.raise_for_status()
    data = resp.json()
    fields = data.get("fields", {})
    summary = fields.get("summary", "")
    description = fields.get("description", "")
    # try common custom field names for acceptance criteria
    acceptance = fields.get("acceptanceCriteria") or fields.get("customfield_acceptance") or ""
    return {"key": key, "summary": summary, "description": description, "acceptance": acceptance}
