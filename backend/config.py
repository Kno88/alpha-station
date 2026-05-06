"""
Alpha Station v4.0 — Configuration
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "matriz", ".env"))


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────────────────────────
    app_name: str = "Alpha Station v4.0"
    debug: bool = False

    # ── ThetaData ────────────────────────────────────────────────────────────
    thetadata_url: str = "http://127.0.0.1:25503"
    thetadata_timeout: int = 10

    # ── Fundamentals ────────────────────────────────────────────────────────
    fmp_api_key: str = os.getenv("FMP_API_KEY", "demo")
    polygon_api_key: str = os.getenv("POLYGON_API_KEY", "")

    # ── Stage Analysis ───────────────────────────────────────────────────────
    ma_short: int = 50
    ma_mid: int = 150
    ma_long: int = 200
    rvol_threshold: float = 2.5       # Stage 2 alert trigger
    rvol_lookback_days: int = 20      # Average volume window

    # ── Alpha Score weights (must sum to 1.0) ────────────────────────────────
    weight_stage: float = 0.30
    weight_rvol: float = 0.15
    weight_fundamental: float = 0.45
    weight_technical: float = 0.10

    # ── PDF ─────────────────────────────────────────────────────────────────
    pdf_output_dir: str = "/tmp/alpha_reports"

    # ── CORS ────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = {"env_prefix": "ALPHA_"}


settings = Settings()
