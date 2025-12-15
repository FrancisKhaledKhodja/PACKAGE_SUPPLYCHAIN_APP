import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    DEBUG = os.getenv("DEBUG", "1") == "1"
    # Frontend dev origin (needed for cookies with CORS + credentials)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000")
    # Point to existing data dir used by current app
    DATA_DIR = os.getenv("DATA_DIR")  # optional override
