# Plan for the AI Test Case Generator

1. Create the config layer first to persist Jira and LLM settings in `config.json`.
2. Build the Settings page for Jira and LLM credentials, keeping tokens and keys masked.
3. Implement Jira fetching using the Jira REST API with clear user-friendly errors.
4. Implement the LLM layer with Ollama primary and automatic Groq fallback.
5. Build the chat page to extract Jira keys, fetch ticket data, build the prompt, and show generated markdown results.
6. Validate the config logic and run a quick smoke test before advising the user to launch the app.
