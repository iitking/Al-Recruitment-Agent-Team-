import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env if present
base_dir = Path(__file__).resolve().parent.parent.parent
env_path = base_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "AI Recruitment Agent Team"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Storage & DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{base_dir / 'backend' / 'recruitment.db'}")
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(base_dir / "backend" / "uploads")))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-recruitment-key")
    
    # LLM Provider Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Calendar & Email
    CALENDAR_TIMEZONE: str = os.getenv("CALENDAR_TIMEZONE", "UTC")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "recruitment@ai-hiring.local")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
