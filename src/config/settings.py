from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # =====================================================
    # API Keys
    # =====================================================
    telegram_api_id: int
    telegram_api_hash: str
    telegram_target_bot: str

    # =====================================================
    # Root Directories
    # =====================================================
    data_dir: Path = ROOT_DIR / "data"
    collector_dir: Path = ROOT_DIR / "src" / "collectors"

    # =====================================================
    # Tracking
    # =====================================================
    tracking_dir: Path = data_dir / "tracking"
    ccdc_tracking_csv: Path = tracking_dir / "ccdc_tracking.csv"

    # =====================================================
    # Raw Data (Collector Inbox)
    # =====================================================
    raw_dir: Path = data_dir / "raw"

    raw_cif_dir: Path = raw_dir / "mof" / "solvents_removed_cif"
    raw_paper_dir: Path = raw_dir / "papers"

    # =====================================================
    # Ready for ETL
    # =====================================================
    ready_dir: Path = data_dir / "ready"

    ready_cif_dir: Path = ready_dir / "cifs"
    ready_paper_dir: Path = ready_dir / "papers"

    # =====================================================
    # CIFs without Papers
    # =====================================================
    no_paper_dir: Path = data_dir / "no_paper"

    no_paper_cif_dir: Path = no_paper_dir / "cifs"

    # =====================================================
    # Processed Data
    # =====================================================
    processed_dir: Path = data_dir / "processed"

    json_dir: Path = processed_dir / "json"
    graph_dir: Path = processed_dir / "graph"
    embeddings_dir: Path = processed_dir / "embeddings"

    # =====================================================
    # Pydantic
    # =====================================================
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env"
    )


settings = Settings()