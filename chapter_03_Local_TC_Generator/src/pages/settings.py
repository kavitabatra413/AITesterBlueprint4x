import streamlit as st
from requests.auth import HTTPBasicAuth
import requests
from config_store import read_config, write_config
from llm_client import check_ollama, check_groq
from jira_client import fetch_ticket

st.set_page_config(page_title="Settings")
st.title("Settings")

cfg = read_config()


def check_jira_connection(base_url: str, user: str, token: str):
    if not base_url:
        return False, "Jira base URL is empty"
    url = f"{base_url.rstrip('/')}/rest/api/2/myself"
    try:
        auth = None
        if user and token:
            auth = HTTPBasicAuth(user, token)
        resp = requests.get(url, auth=auth, timeout=10)
        if resp.status_code == 200:
            return True, "Connected successfully"
        if resp.status_code in (401, 403):
            return False, "Authentication failed"
        return False, f"HTTP {resp.status_code}"
    except Exception as exc:
        return False, str(exc)


with st.form("settings_form"):
    jira_base = st.text_input("Jira Base URL", value=cfg.get("jira_base", ""))
    jira_user = st.text_input("Jira User/Email", value=cfg.get("jira_user", ""))
    jira_token = st.text_input("Jira Token/API Token", value=cfg.get("jira_token", ""))
    ollama_url = st.text_input("Ollama URL", value=cfg.get("ollama_url", "http://127.0.0.1:11434"))
    ollama_model = st.text_input("Ollama Model", value=cfg.get("ollama_model", "gemma3:1b"))
    ollama_token = st.text_input("Ollama Token", value=cfg.get("ollama_token", ""))
    groq_api_key = st.text_input("Groq API Key", value=cfg.get("groq_api_key", ""))
    llm_provider = st.radio(
        "LLM Provider",
        options=["ollama", "groq"],
        index=0 if str(cfg.get("llm_provider", "ollama")).lower() == "ollama" else 1,
        horizontal=True,
    )
    submitted = st.form_submit_button("Save")
    if submitted:
        new = {
            "jira_base": jira_base,
            "jira_user": jira_user,
            "jira_token": jira_token,
            "ollama_url": ollama_url,
            "ollama_model": ollama_model,
            "ollama_token": ollama_token,
            "groq_api_key": groq_api_key,
            "llm_provider": llm_provider,
        }
        write_config(new)
        st.success("Saved config.json")

st.header("Test Connections")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Check Ollama"):
        ok = check_ollama()
        st.write("Ollama:", "OK" if ok else "Unavailable")
with col2:
    if st.button("Check Groq"):
        ok = check_groq()
        st.write("Groq reachable:", ok)
with col3:
    if st.button("Check Jira"):
        ok, message = check_jira_connection(jira_base, jira_user, jira_token)
        st.write("Jira:", "OK" if ok else "Unavailable")
        st.write(message)

st.header("Test Jira Fetch")
test_key = st.text_input("Sample Jira Key (for testing)")
if st.button("Fetch Ticket") and test_key:
    try:
        ticket = fetch_ticket(test_key)
        st.json(ticket)
    except Exception as e:
        st.error(f"Fetch failed: {e}")
