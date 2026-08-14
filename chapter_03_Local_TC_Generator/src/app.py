import re
from pathlib import Path
import streamlit as st
from config_store import read_config
from jira_client import fetch_ticket
from llm_client import generate, check_ollama, check_groq

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR.parent / "templates" / "testcase_creator.md"

st.set_page_config(page_title="Jira Test Case Generator")

st.title("Jira Test Case Generator")

cfg = read_config()

col1, col2 = st.columns([3,1])
with col1:
    user_input = st.text_area("Prompt or Jira key", height=120, placeholder="create test cases for JIRA-102")
with col2:
    if st.button("Generate"):
        # find Jira key
        key_match = re.search(r"\b[A-Z]+-\d+\b", user_input or "")
        if key_match:
            key = key_match.group(0)
            st.info(f"Fetching ticket {key}...")
            try:
                ticket = fetch_ticket(key)
            except Exception as e:
                st.error(f"Failed to fetch ticket: {e}")
                ticket = None
        else:
            ticket = None

        # load template
        template = ""
        if TEMPLATE_PATH.exists():
            template = TEMPLATE_PATH.read_text(encoding="utf-8")

        prompt = user_input or "Please generate test cases."
        if ticket:
            prompt = template + "\n\n" + "\n".join([f"Summary: {ticket.get('summary')}", f"Description: {ticket.get('description')}", f"Acceptance Criteria: {ticket.get('acceptance')}"])

        st.info("Generating via LLM...")
        out = generate(prompt)
        st.subheader("Generated Test Cases")
        st.code(out)

with st.sidebar:
    st.header("Providers")
    selected = str(cfg.get("llm_provider", "ollama")).lower()
    provider_name = "Groq" if selected == "groq" else "Ollama"
    st.radio("Selected LLM", options=["ollama", "groq"], index=0 if selected == "ollama" else 1, horizontal=True, key="selected_llm")
    st.write("Ollama local:", "OK" if check_ollama() else "Unavailable")
    st.write("Groq configured:", "Yes" if check_groq() else "No")
    st.write("Active provider:", provider_name)
    st.divider()
    st.header("Loaded Config")
    st.write("Jira Base:", cfg.get("jira_base", ""))
    st.write("Jira User:", cfg.get("jira_user", ""))
    st.write("Ollama URL:", cfg.get("ollama_url", ""))
    st.write("Ollama Model:", cfg.get("ollama_model", ""))
    st.write("Groq API Key:", "SET" if cfg.get("groq_api_key") else "EMPTY")
