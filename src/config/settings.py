from pathlib import Path
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[2]


class ExtractorSettings(BaseSettings):
        mode: str = "fast"
        output_format: str = "json"
        use_llm: bool = True
        llm_service: str = "marker.services.openai.OpenAIService"
        openai_base_url: str = "http://localhost:11434/v1"
        openai_api_key: str = "ollama"
        openai_model: str = "gemma4:e4b"
        block_correction_prompt: bool = True






class Settings(BaseSettings):


    # Root Directories
    data_dir: Path = ROOT_DIR / "data"
    collector_dir: Path = ROOT_DIR / "src" / "collectors"


    # Tracking
    tracking_dir: Path = data_dir / "tracking"
    ccdc_tracking_csv: Path = tracking_dir / "ccdc_tracking.csv"
    paper_tracking_csv: Path = tracking_dir / "paper_tracking.csv"


    # Raw Data (Collector Inbox)
    raw_dir: Path = data_dir / "raw"

    raw_cif_dir: Path = raw_dir / "mof" / "solvents_removed_cif"
    raw_paper_dir: Path = raw_dir / "papers"


    # Ready for ETL
    ready_dir: Path = data_dir / "ready"

    ready_cif_dir: Path = ready_dir / "cifs"
    ready_paper_dir: Path = ready_dir / "papers"


    # CIFs without Papers
    no_paper_dir: Path = data_dir / "no_paper"

    no_paper_cif_dir: Path = no_paper_dir / "cifs"


    # Processed Data
    processed_dir: Path = data_dir / "processed"