from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "AI Video Vietnamese Dubber"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: Path = Path("./temp_files")
    OUTPUT_DIR: Path = Path("./outputs")
    CORS_ALLOW_ORIGINS: list = ["*"]
    TEMP_FILE_EXPIRE_MINUTES: int = 30
    VOICE_NAME: str = "vi-VN-HoaiAnNeural"
    WHISPER_MODEL: str = "base"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)

settings = Settings()
