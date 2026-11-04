from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    index_path: Path = Path("index.bin")
    corpus_path: Path = Path("data/corpus")
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_prefix = "FINDEX_"
        env_file = ".env"

settings = Settings()