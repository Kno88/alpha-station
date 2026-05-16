"""
Alpha Station v6.0 — Configuration
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load local .env if it exists
load_dotenv()


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "Alpha Station v6.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    # ── Fundamentals ───────────────────────────────────────────────────────────
    fmp_api_key: str = os.getenv("FMP_API_KEY", "demo")
    polygon_api_key: str = os.getenv("POLYGON_API_KEY", "")

    # ── Stage Analysis ─────────────────────────────────────────────────────────
    ma_short: int = 50
    ma_mid: int = 150
    ma_long: int = 200
    rvol_threshold: float = 2.5       # Stage 2 alert trigger
    rvol_lookback_days: int = 20      # Average volume window

    # ── RS Line (v5.0) ────────────────────────────────────────────────────────
    rs_benchmark: str = "SPY"         # Benchmark for RS Line
    rs_lookback_days: int = 252       # 1 year for RS Rating
    rs_new_high_lookback: int = 252   # RS new high detection window
    rs_near_high_pct: float = 0.05    # Within 5% = "near high"

    # ── Risk Management (v5.0) ───────────────────────────────────────────────
    default_portfolio_size: float = 100_000.0  # Default portfolio in USD
    max_risk_per_trade_pct: float = 0.01       # 1% max risk per trade
    max_position_pct: float = 0.10             # 10% max position size
    atr_stop_multiplier: float = 2.0           # Stop = price - (ATR * multiplier)
    reward_risk_target: float = 3.0            # Target 3:1 R:R minimum

    # ── Alpha Score weights (must sum to 1.0) ───────────────────────────────
    weight_stage: float = 0.25
    weight_rs_line: float = 0.20
    weight_fundamental: float = 0.40
    weight_rvol: float = 0.15

    # ── PDF ───────────────────────────────────────────────────────────────────
    pdf_output_dir: str = os.getenv("PDF_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "alpha_reports"))

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Allow overriding CORS origins via ALPHA_CORS_ORIGINS (comma separated)
    cors_origins: list[str] = os.getenv(
        "ALPHA_CORS_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    model_config = {"env_prefix": "ALPHA_"}


settings = Settings()
