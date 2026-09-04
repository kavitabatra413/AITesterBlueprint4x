import re
from pathlib import Path

import streamlit as st

from config_store import load_config
from jira_client import fetch_ticket
from llm_client import check_ollama, generate_test_cases

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR.parent / 'templates' / 'testcase_creator.md'
TEMPLATE_OUTPUT_PATH = BASE_DIR.parent / 'templates' / 'testcase_template.md'

st.set_page_config(page_title='AI Test Case Generator', page_icon='🧪')
st.title('AI Test Case Generator')

config = load_config()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header('Navigation')
    st.page_link('pages/settings.py', label='Open Settings')

st.subheader('Chat')

for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

prompt = st.chat_input('Type a Jira request, for example: Create test cases for QA-102')

if prompt:
    key_match = re.search(r'\b[A-Z]+-\d+\b', prompt)
    if not key_match:
        response = 'I could not find a valid Jira key in your message. Please use a format like QA-102.'
        st.session_state.chat_history.append({'role': 'user', 'content': prompt})
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        st.rerun()

    ticket_key = key_match.group(0)
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})

    try:
        ticket = fetch_ticket(ticket_key, config)
        template_text = TEMPLATE_PATH.read_text(encoding='utf-8') if TEMPLATE_PATH.exists() else ''
        output_template = TEMPLATE_OUTPUT_PATH.read_text(encoding='utf-8') if TEMPLATE_OUTPUT_PATH.exists() else ''

        final_prompt = (
            f"{template_text}\n\n"
            "--- Jira Ticket: " + ticket_key + " ---\n\n"
            f"Summary:\n{ticket['summary']}\n\n"
            f"Description:\n{ticket['description']}\n\n"
            f"Acceptance Criteria:\n{ticket['acceptance_criteria']}\n\n"
            f"Priority:\n{ticket['priority']}\n\n"
            f"Issue Type:\n{ticket['issue_type']}\n\n"
            "Use the output format and structure described in the template.\n"
            "Do not invent requirements that are not present in the Jira ticket.\n"
            "Test case IDs must follow the format TC-001, TC-002, etc.\n"
            f"{output_template}"
        )

        if str(config.get('llm_provider', 'ollama')).lower() == 'ollama' and not check_ollama(config):
            st.warning('Ollama is unavailable, so the app automatically switched to Groq for this request.')

        generated = generate_test_cases(final_prompt, config)
        if not generated or not str(generated).strip():
            raise ValueError('LLM returned an invalid or empty response.')

        with st.chat_message('assistant'):
            st.markdown(generated)
        st.session_state.chat_history.append({'role': 'assistant', 'content': generated})
    except Exception as exc:
        error_message = str(exc) or 'Something went wrong while generating test cases.'
        with st.chat_message('assistant'):
            st.markdown(f'⚠️ {error_message}')
        st.session_state.chat_history.append({'role': 'assistant', 'content': f'⚠️ {error_message}'})
