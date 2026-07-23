from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    telegram_api_id: int
    telegram_api_hash: str
    telegram_target_bot: str

    data_dir: Path = ROOT_DIR / "data"
    collector_dir: Path = ROOT_DIR / "src" / "collectors"

    tracking_dir: Path = data_dir / "tracking"
    raw_dir: Path = data_dir / "raw"

    cif_dir: Path = raw_dir / "cifs"
    raw_paper_dir: Path = raw_dir / "papers"

    model_config = SettingsConfigDict(
        env_file= ROOT_DIR / ".env"
    )

print(ROOT_DIR)
print((ROOT_DIR / ".env").exists())


settings = Settings()
print(ROOT_DIR)