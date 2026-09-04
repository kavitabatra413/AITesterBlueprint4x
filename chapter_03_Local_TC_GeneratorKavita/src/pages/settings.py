import streamlit as st

from config_store import load_config, save_config


st.set_page_config(page_title='Settings', page_icon='⚙️')


def _mask(value):
    if not value:
        return ''
    if len(value) <= 6:
        return '*' * len(value)
    return value[:2] + '*' * (len(value) - 4) + value[-2:]


config = load_config()

st.title('Settings')
st.caption('Store Jira details and default LLM settings locally on this machine.')

with st.form('settings_form'):
    jira_base_url = st.text_input('Jira Base URL', value=config.get('jira_base_url', ''), help='Example: https://company.atlassian.net')
    jira_email = st.text_input('Jira Email', value=config.get('jira_email', ''), type='default')
    jira_api_token = st.text_input('Jira API Token', value=config.get('jira_api_token', ''), type='password')
    llm_provider = st.selectbox('LLM Provider', ['Ollama', 'Groq'], index=0 if str(config.get('llm_provider', 'ollama')).lower() == 'ollama' else 1)
    groq_api_key = st.text_input('Groq API Key', value=config.get('groq_api_key', ''), type='password')

    save_clicked = st.form_submit_button('Save settings')
    if save_clicked:
        payload = {
            'jira_base_url': jira_base_url,
            'jira_email': jira_email,
            'jira_api_token': jira_api_token,
            'llm_provider': 'ollama' if llm_provider == 'Ollama' else 'groq',
            'groq_api_key': groq_api_key,
        }
        save_config(payload)
        st.success('Settings saved locally in config.json')

st.subheader('Saved values')
st.write('Jira Base URL:', jira_base_url or 'Not set')
st.write('Jira Email:', jira_email or 'Not set')
st.write('Jira API Token:', _mask(jira_api_token) if jira_api_token else 'Not set')
st.write('LLM Provider:', llm_provider)
st.write('Groq API Key:', _mask(groq_api_key) if groq_api_key else 'Not set')
