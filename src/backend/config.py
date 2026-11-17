import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""
    
    # HTTP server port and debug mode (used for local standalone execution)
    PORT = int(os.getenv("PORT", "5001"))
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    # PostgreSQL database connection URL (defaults to localhost for standalone dev)
    _raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/qr_codes_db"
    )
    
    # SQLAlchemy 2.0 requires an explicit dialect specification (psycopg2) for PostgreSQL
    if _raw_db_url.startswith("postgresql://"):
        DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        DATABASE_URL = _raw_db_url
