You are a senior AI developer and build this application for me from scratch

You will handle the implementation, debugging, and technical decisions. Explain everything in simple terms because I am a QA engineer, not a developer.

APPLICATION NAME:
AI Test Case Generator

GOAL:
Build a local Streamlit application where I can enter a Jira ticket such as "Create test cases for KAN-2". The application should fetch the Jira ticket details, send them to an LLM using my existing test-case generation templates, and display the generated test cases.

IMPORTANT:
Before writing any code, inspect the existing repository and understand these files if they exist:

- finetuned_prompt.md
- Templates/test_creater.md
- Templates/testcase_template.md
- plan.md

Treat the existing templates as the source of truth for test-case generation and output format. Do not replace or change their behavior unnecessarily.

PROJECT STRUCTURE:

Local_Testcase_Generator/
├── Src/
│ ├── app.py
│ ├── config_store.py
│ ├── jira_client.py
│ ├── llm_client.py
│ ├── pages/
│ │ └── settings.py
│ ├── requirements.txt
│ ├── .gitignore
│ ├── finetuned_prompt.md
│ └── plan.md
├── Templates/
│ ├── test_creater.md
│ └── testcase_template.md

SCREEN 1 — CHAT

Create a Streamlit chat interface.

Title:
AI Test Case Generator

The screen should contain:

- Chat history
- Chat input
- Send button/action
- Navigation to Settings

Example user input:

Create test cases for QA-102

When I submit this:

1. Extract the Jira ticket key using:
 r'\b[A-Z]+-\d+\b'

2. Fetch the Jira ticket.

3. Extract:
 - Summary
 - Description
 - Acceptance Criteria
 - Priority
 - Issue Type

4. Load Templates/test_creater.md.

5. Combine the template instructions with the Jira ticket information.

6. Send the final prompt to the configured LLM.

7. Generate test cases.

8. Display the result in the chat interface as Markdown.

SETTINGS SCREEN:

Create a Settings page.

Fields:

- Jira Base URL
- Jira Email
- Jira API Token
- LLM Provider
- Groq API Key

LLM Provider options:

- Ollama
- Groq

API tokens and API keys must be masked.

Save the configuration locally in:

config.json

Never hardcode credentials.

CONFIGURATION:

Create config_store.py.

Implement:

load_config()
save_config(data)
get(key, default=None)

If config.json does not exist, return an empty configuration.

JIRA INTEGRATION:

Create jira_client.py.

Implement:

fetch_ticket(ticket_key, config)

Use:

GET {jira_url}/rest/api/3/issue/{ticket_key}

Use Jira email and API token for authentication.

Return:

summary
description
acceptance_criteria
priority
issue_type

Handle these errors clearly:

- Invalid credentials
- Ticket not found
- Jira unavailable
- Network failure
- Invalid configuration
- Unexpected Jira response

Do not expose credentials in error messages.

LLM INTEGRATION:

Create llm_client.py.

Implement:

generate_test_cases(prompt, config)

Primary provider:

Ollama

Use:

http://localhost:11434/api/generate

Model:

gemma3:1b

Use requests rather than an Ollama SDK.

If Ollama is unavailable because of connection failure or timeout, automatically fall back to Groq.

Groq should use the Groq API key stored in configuration.

Use an available supported Groq model.

Tell me clearly in the UI when the application has fallen back from Ollama to Groq.

Return the generated response as Markdown.

PROMPT CONSTRUCTION:

Load:

Templates/test_creater.md

Build the final prompt using:

1. Existing instructions from test_creater.md
2. Jira ticket information
3. Existing testcase_template.md/output requirements

The Jira information should look like:

--- Jira Ticket: {ticket_key} ---

Summary:
{summary}

Description:
{description}

Acceptance Criteria:
{acceptance_criteria}

Priority:
{priority}

Issue Type:
{issue_type}

Do not invent information that does not exist in the Jira ticket.

TEST CASE OUTPUT:

Use the existing testcase_template.md and test_creater.md format.

Test case IDs should follow the existing format, for example:

TC-001
TC-002
TC-003

Do not generate a fixed number of test cases. Generate appropriate coverage based on the ticket and acceptance criteria.

DEPENDENCIES:

Keep dependencies minimal.

requirements.txt:

streamlit>=1.35.0
requests>=2.31.0
groq>=0.9.0

Do not add unnecessary packages.

GITIGNORE:

Create/update .gitignore:

config.json
__pycache__/
*.pyc
.env
env.md

SECURITY:

- Never hardcode credentials.
- Never print API keys or tokens.
- Never commit config.json.
- Mask credentials in the Settings screen.
- Do not send Jira credentials to the LLM.
- Send only the required Jira ticket information to the LLM.

ERROR HANDLING:

The application should provide simple, understandable messages when:

- Jira credentials are missing
- Jira authentication fails
- Jira ticket does not exist
- Jira is unavailable
- Ollama is unavailable
- Groq fails
- LLM configuration is missing
- Jira ticket key is invalid
- Jira description is empty
- Acceptance criteria are missing
- LLM returns an invalid/empty response

Do not show technical stack traces to normal users unless needed for debugging.

BUILD ORDER:

Build the application one module at a time.

Step 1:
config_store.py

Step 2:
pages/settings.py

Step 3:
jira_client.py

Step 4:
llm_client.py

Step 5:
app.py

Step 6:
requirements.txt and .gitignore

IMPORTANT FOR ME:

I am not a programmer.

After completing each step:

1. Explain in simple language what you built.
2. Tell me exactly how to run or test it.
3. Tell me exactly what result I should see.
4. If I need to run a command, give me the exact command to copy and paste.
5. Do not assume I know Python, Streamlit, virtual environments, APIs, Git, or terminals.
6. If an error occurs, ask me to provide the error and diagnose it.
7. Prefer fixing the problem yourself rather than asking me to modify code manually.
8. Never ask me to make a code change without giving me the exact code and exact location.
9. Keep explanations short and simple.

DO NOT:

- Add authentication for the Streamlit application.
- Add a database.
- Add Docker.
- Add deployment configuration.
- Add unnecessary APIs.
- Add unnecessary LLM providers.
- Add unnecessary dependencies.
- Build features that are not requested.
- Modify existing prompt/template files unless necessary.

FINAL VALIDATION:

After implementation, guide me through this complete test:

1. Start the Streamlit application.
2. Open Settings.
3. Enter Jira URL.
4. Enter Jira email.
5. Enter Jira API token.
6. Select Ollama.
7. Save settings.
8. Return to Chat.
9. Enter:

Create test cases for QA-102

10. Verify that QA-102 is extracted.
11. Verify that Jira details are fetched.
12. Verify that the existing test-case template is loaded.
13. Verify that the final prompt is constructed.
14. Verify that Ollama generates test cases.
15. Verify that the generated test cases appear in the chat.
16. Stop Ollama and verify that the application automatically falls back to Groq.
17. Verify that credentials are never displayed.

MOST IMPORTANT:

Do not try to build the entire application blindly in one step.

First inspect the existing project and files.

Then create a simple implementation plan.

Then build one module at a time.

After each module, validate it before moving to the next module.

Act as my developer while I act as the QA/End user of application.(Edited)
