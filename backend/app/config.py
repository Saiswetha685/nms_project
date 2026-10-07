import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    PROJECT_NAME: str = "SLA-Predict Network Management System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    MONGODB_URI: str = Field(default_factory=lambda: os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    DATABASE_NAME: str = Field(default_factory=lambda: os.getenv("DATABASE_NAME", "sla_predict_db"))

    JWT_SECRET: str = Field(default_factory=lambda: os.getenv("JWT_SECRET", "sla-predict-super-secret-key-college-demo-2026"))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("JWT_EXPIRE_MINUTES", "1440")))

    ANTHROPIC_API_KEY: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))

    SMTP_HOST: str = Field(default_factory=lambda: os.getenv("SMTP_HOST", ""))
    SMTP_PORT: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    SMTP_USERNAME: str = Field(default_factory=lambda: os.getenv("SMTP_USERNAME", ""))
    SMTP_PASSWORD: str = Field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    SMTP_FROM: str = Field(default_factory=lambda: os.getenv("SMTP_FROM", "alerts@slapredict.io"))

    FRONTEND_URL: str = Field(default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:5173"))
    DEMO_MODE: bool = Field(default_factory=lambda: os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes"))

    ML_MODELS_DIR: Path = Path(__file__).resolve().parent.parent / "ml_models"

settings = Settings()
settings.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
