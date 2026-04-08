from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ihub:changeme@db:5432/identityhub"

    # App security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Jira OAuth 2.0 (3LO)
    JIRA_ENCRYPTION_KEY: str
    JIRA_CLIENT_ID: str = ""
    JIRA_CLIENT_SECRET: str = ""
    JIRA_REDIRECT_URI: str = "http://localhost:8000/jira/auth/callback"

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # LLM / Ollama (blog digest bonus)
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "llama3.2"

    # Blog digest configuration
    BLOG_DIGEST_PROJECT_KEY: str = "SEC"
    BLOG_DIGEST_USER_EMAIL: str | None = None

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()
