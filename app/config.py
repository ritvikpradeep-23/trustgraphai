"""All tunable settings, read from environment variables (or a .env file).

Every limit and threshold lives here so they can be changed without touching
code. Variable names are the field names in capitals, e.g. SCAM_HIGH_THRESHOLD.
See .env.example for the full list with explanations.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- CORS: which web pages may call this API from a browser ---------------
    # Comma-separated. A browser extension's origin looks like
    # chrome-extension://<extension id>; add it here once you know the id.
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:8000"

    # --- Scam correlation (Milestone 1) ---------------------------------------
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    reports_path: str = "data/scam_reports.json"  # where reports persist between restarts
    scam_high_threshold: float = 0.82    # top similarity at or above this -> HIGH
    scam_medium_threshold: float = 0.68  # at or above this -> MEDIUM, below -> LOW
    scam_top_k: int = 5                  # how many nearest reports to look at
    max_text_chars: int = 5000

    # --- Deepfake video (Milestone 2) -----------------------------------------
    deepfake_model_path: str = ""        # e.g. models/deepfake.pt (TorchScript); empty = not configured
    deepfake_mock: bool = False          # DEEPFAKE_MOCK=1 enables a fake model for demos only
    deepfake_input_size: int = 224       # face crops are resized to this square before the model
    video_max_bytes: int = 50 * 1024 * 1024   # 50 MB
    video_max_seconds: float = 60.0
    video_sample_fps: float = 1.0        # frames looked at per second of video
    video_max_frames: int = 30           # hard cap, keeps a request fast
    face_margin: float = 0.2             # extra border around a face crop (fraction of face size)
    frame_fake_threshold: float = 0.5    # a frame counts as "fake" at or above this score
    video_fake_ratio_threshold: float = 0.5  # video is likely_fake if this share of face frames are fake

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """One Settings object per process (environment is read once)."""
    return Settings()
