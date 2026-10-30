"""
Configuração central do jobs-bot.
Carrega variáveis de ambiente e expõe constantes do sistema.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Database ---
DATABASE_PATH = BASE_DIR / "data" / "jobs_bot.db"

# --- Scraping ---
REQUEST_TIMEOUT = 30  # segundos
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

# --- Scheduler ---
SEARCH_INTERVAL_HOURS = int(os.getenv("SEARCH_INTERVAL_HOURS", "12"))
WEEKDAYS_ONLY = os.getenv("WEEKDAYS_ONLY", "true").lower() in ("true", "1", "yes")

# --- Matching ---
MIN_MATCH_SCORE = float(os.getenv("MIN_MATCH_SCORE", "0.15"))  # 15% de match mínimo

# --- Fontes de vagas habilitadas ---
ENABLED_SOURCES = [
    s.strip()
    for s in os.getenv(
        "ENABLED_SOURCES",
        "remotive,github,programathor,remoteok,himalayas,weworkremotely,wellfound,geekhunter"
    ).split(",")
    if s.strip()
]


def validate() -> None:
    """Garante que as variáveis obrigatórias estejam presentes."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN não configurado no .env!\n"
            "Crie um bot com @BotFather no Telegram e cole o token."
        )