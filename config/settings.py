"""
Configuration management for TikTok Viral Signal Detector.
Loads settings from environment variables with validation.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="tiktok_viral_detector", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")

    @property
    def database_url(self) -> str:
        """Construct database URL from components or use provided URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ==========================================================================
    # TikTok API Configuration
    # ==========================================================================
    TIKTOK_MS_TOKEN: str = Field(default="", env="TIKTOK_MS_TOKEN")
    PROXY_URL: Optional[str] = Field(default=None, env="PROXY_URL")

    # ==========================================================================
    # Google Gemini API
    # ==========================================================================
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash-exp", env="GEMINI_MODEL")
    GEMINI_TEMPERATURE: float = Field(default=0.7, env="GEMINI_TEMPERATURE")
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=1024, env="GEMINI_MAX_OUTPUT_TOKENS")

    # ==========================================================================
    # File Storage Paths
    # ==========================================================================
    VIDEO_STORAGE_PATH: str = Field(default="/tmp/videos", env="VIDEO_STORAGE_PATH")
    EMBEDDING_STORAGE_PATH: str = Field(default="./data/processed/embeddings", env="EMBEDDING_STORAGE_PATH")
    TRANSCRIPT_STORAGE_PATH: str = Field(default="./data/processed/transcripts", env="TRANSCRIPT_STORAGE_PATH")
    CHROMADB_PATH: str = Field(default="./data/chromadb", env="CHROMADB_PATH")

    # ==========================================================================
    # Model Paths
    # ==========================================================================
    XGBOOST_MODEL_PATH: str = Field(default="./data/models/xgboost_model.pkl", env="XGBOOST_MODEL_PATH")
    NEURAL_NET_MODEL_PATH: str = Field(default="./data/models/neural_net_model.pkl", env="NEURAL_NET_MODEL_PATH")
    SCALER_PATH: str = Field(default="./data/models/feature_scaler.pkl", env="SCALER_PATH")

    # ==========================================================================
    # Scraping Configuration
    # ==========================================================================
    MIN_REQUEST_DELAY: int = Field(default=5, env="MIN_REQUEST_DELAY")
    MAX_REQUEST_DELAY: int = Field(default=10, env="MAX_REQUEST_DELAY")
    MAX_VIDEOS_PER_CREATOR: int = Field(default=15, env="MAX_VIDEOS_PER_CREATOR")
    MAX_RETRY_ATTEMPTS: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    RETRY_BACKOFF_MULTIPLIER: int = Field(default=2, env="RETRY_BACKOFF_MULTIPLIER")

    # ==========================================================================
    # Video Processing Configuration
    # ==========================================================================
    FRAME_EXTRACTION_FPS: int = Field(default=3, env="FRAME_EXTRACTION_FPS")
    MAX_VIDEO_DURATION: int = Field(default=180, env="MAX_VIDEO_DURATION")
    HOOK_ANALYSIS_WINDOW: int = Field(default=3, env="HOOK_ANALYSIS_WINDOW")

    # ==========================================================================
    # ML Model Configuration
    # ==========================================================================
    VIRAL_PROBABILITY_THRESHOLD: float = Field(default=0.7, env="VIRAL_PROBABILITY_THRESHOLD")
    NEURAL_NET_WEIGHT: float = Field(default=0.6, env="NEURAL_NET_WEIGHT")
    XGBOOST_WEIGHT: float = Field(default=0.4, env="XGBOOST_WEIGHT")
    MIN_CONFIDENCE_THRESHOLD: float = Field(default=0.5, env="MIN_CONFIDENCE_THRESHOLD")

    # ==========================================================================
    # Feature Engineering Configuration
    # ==========================================================================
    ENGAGEMENT_ANALYSIS_WINDOW_DAYS: int = Field(default=30, env="ENGAGEMENT_ANALYSIS_WINDOW_DAYS")
    MIN_VIDEOS_FOR_PREDICTION: int = Field(default=5, env="MIN_VIDEOS_FOR_PREDICTION")
    GROWTH_ZSCORE_THRESHOLD: float = Field(default=2.0, env="GROWTH_ZSCORE_THRESHOLD")

    # ==========================================================================
    # Logging Configuration
    # ==========================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE_PATH: str = Field(default="./logs/app.log", env="LOG_FILE_PATH")
    DEBUG_MODE: bool = Field(default=False, env="DEBUG_MODE")

    # ==========================================================================
    # Streamlit Configuration
    # ==========================================================================
    STREAMLIT_SERVER_PORT: int = Field(default=8501, env="STREAMLIT_SERVER_PORT")
    STREAMLIT_SERVER_ADDRESS: str = Field(default="localhost", env="STREAMLIT_SERVER_ADDRESS")
    ENABLE_STREAMLIT_CACHE: bool = Field(default=True, env="ENABLE_STREAMLIT_CACHE")

    # ==========================================================================
    # Development/Production Settings
    # ==========================================================================
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    SAFE_MODE: bool = Field(default=False, env="SAFE_MODE")

    # Agent enable/disable flags
    ENABLE_SCRAPER_AGENT: bool = Field(default=True, env="ENABLE_SCRAPER_AGENT")
    ENABLE_VIDEO_ANALYSIS_AGENT: bool = Field(default=True, env="ENABLE_VIDEO_ANALYSIS_AGENT")
    ENABLE_ENGAGEMENT_AGENT: bool = Field(default=True, env="ENABLE_ENGAGEMENT_AGENT")
    ENABLE_PREDICTION_AGENT: bool = Field(default=True, env="ENABLE_PREDICTION_AGENT")
    ENABLE_REPORT_AGENT: bool = Field(default=True, env="ENABLE_REPORT_AGENT")

    # ==========================================================================
    # Security Settings
    # ==========================================================================
    SECRET_KEY: str = Field(default="development-secret-key-change-in-production", env="SECRET_KEY")
    API_RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="API_RATE_LIMIT_PER_MINUTE")

    # ==========================================================================
    # Experimental Features
    # ==========================================================================
    ENABLE_REAL_TIME_MONITORING: bool = Field(default=False, env="ENABLE_REAL_TIME_MONITORING")
    ENABLE_MULTI_PLATFORM: bool = Field(default=False, env="ENABLE_MULTI_PLATFORM")
    ENABLE_COMPETITOR_ANALYSIS: bool = Field(default=False, env="ENABLE_COMPETITOR_ANALYSIS")

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v.lower()

    def create_directories(self):
        """Create required directories if they don't exist."""
        directories = [
            self.VIDEO_STORAGE_PATH,
            self.EMBEDDING_STORAGE_PATH,
            self.TRANSCRIPT_STORAGE_PATH,
            self.CHROMADB_PATH,
            Path(self.LOG_FILE_PATH).parent,
            Path(self.XGBOOST_MODEL_PATH).parent,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the settings singleton instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings


# Convenience function to reload settings
def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    _settings.create_directories()
    return _settings


if __name__ == "__main__":
    # Test settings loading
    settings = get_settings()
    print("Settings loaded successfully!")
    print(f"Database URL: {settings.database_url}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Video Storage: {settings.VIDEO_STORAGE_PATH}")
