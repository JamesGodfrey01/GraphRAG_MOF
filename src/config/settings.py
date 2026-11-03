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