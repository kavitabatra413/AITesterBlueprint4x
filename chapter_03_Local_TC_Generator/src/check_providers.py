from config_store import read_config
from llm_client import check_ollama, check_groq, generate
 
def main():
    cfg = read_config()
    print('jira_base   =', cfg.get('jira_base'))
    print('jira_user   =', cfg.get('jira_user'))
    print('jira_token  =', 'SET' if cfg.get('jira_token') else 'EMPTY')
    print('ollama_url  =', cfg.get('ollama_url'))
    print('ollama_model=', cfg.get('ollama_model'))
    print('ollama_token=', 'SET' if cfg.get('ollama_token') else 'EMPTY')
    print('groq_api_key=', 'SET' if cfg.get('groq_api_key') else 'EMPTY')
    print('check_ollama ->', check_ollama())
    print('check_groq  ->', check_groq())
    print('generate test ->')
    print(generate('Say hello from the test app.', timeout=10))

if __name__ == '__main__':
    main()
