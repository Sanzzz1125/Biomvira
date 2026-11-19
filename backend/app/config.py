"""
NutriLens Application Configuration
Loads settings from environment variables or a local .env file.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))


class Settings(BaseSettings):
    # --- Application ---
    app_name: str = "NutriLens"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Database ---
    # Production: the Neon Postgres connection string (DATABASE_URL in Render / backend/.env).
    # Local fallback when unset: a SQLite file inside backend/ (handy for offline development).
    database_url: str = f"sqlite:///{os.path.join(BACKEND_DIR, 'nutrilens.db')}"
    # Apply pending Alembic migrations when the server starts (single-instance deployments).
    auto_migrate: bool = True

    # --- LLM Fallback (Gemini) ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # --- Assistant language model (optional) ---
    # Any OpenAI-compatible chat API. The default is Groq's free plan (no card needed, no data kept by default);
    # set GROQ_API_KEY to turn it on. Without a key the assistant answers from its rule-based knowledge only.
    groq_api_key: str = ""
    chat_llm_api_key: str = ""   # for another provider; takes precedence over groq_api_key
    chat_llm_base_url: str = "https://api.groq.com/openai/v1"
    # Tried in order; when one is rate-limited or down the next is used, then the rule-based answer.
    chat_llm_models: str = "openai/gpt-oss-120b,qwen/qwen3.8-27b,openai/gpt-oss-20b"
    chat_llm_timeout_seconds: float = 12.0

    max_upload_bytes: int = 10 * 1024 * 1024
    max_report_pages: int = 20
    max_image_pixels: int = 20_000_000
    max_text_chars: int = 200_000
    processing_timeout_seconds: int = 90
    ocr_timeout_seconds: int = 15
    max_parallel_reports: int = 2
    gemini_timeout_ms: int = 15000

    # --- Auth & sessions ---
    session_cookie_name: str = "nl_session"
    csrf_cookie_name: str = "nl_csrf"
    session_ttl_days: int = 7
    # Must be true in production (HTTPS). Locally the site runs on plain http.
    cookie_secure: bool = False
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    link_ttl_hours: int = 48          # invite and password-reset links
    auth_rate_limit_per_minute: int = 10

    # --- CORS ---
    # Comma-separated list of allowed origins. In production the frontend reaches the API through
    # Vercel's /api rewrite (same origin), so CORS is only needed for local tooling.
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- PDF Export ---
    pdf_brand_color: str = "#2563EB"
    pdf_logo_path: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        """Neon/Render hand out postgres:// URLs; SQLAlchemy needs the psycopg 3 driver name."""
        url = self.database_url.strip()
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    def get_allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


# Singleton instance — import this everywhere
settings = Settings()
