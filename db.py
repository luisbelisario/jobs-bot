"""
Camada de persistência — SQLite assíncrono.
Guarda perfil do usuário e vagas já notificadas (evita duplicatas).
"""
import aiosqlite
from typing import Optional
from config import DATABASE_PATH

DB = None  # conexão global, iniciada em init_db()


async def init_db() -> None:
    """Cria o banco e as tabelas se não existirem."""
    global DB
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB = await aiosqlite.connect(str(DATABASE_PATH))
    DB.row_factory = aiosqlite.Row
    await DB.executescript("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            raw_text TEXT,
            skills TEXT,
            experience_years INTEGER,
            desired_roles TEXT,
            locations TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notified_jobs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            url TEXT,
            notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS search_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            jobs_found INTEGER DEFAULT 0,
            jobs_matched INTEGER DEFAULT 0,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id TEXT PRIMARY KEY,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    await DB.commit()


async def close_db() -> None:
    """Fecha a conexão com o banco."""
    if DB:
        await DB.close()


# --- Perfil do usuário ---

async def save_user_profile(
    raw_text: str,
    skills: str,
    experience_years: int,
    desired_roles: str,
    locations: str,
) -> None:
    """Salva ou atualiza o perfil do usuário (único registro)."""
    await DB.execute("DELETE FROM user_profile")
    await DB.execute(
        "INSERT INTO user_profile (raw_text, skills, experience_years, desired_roles, locations) "
        "VALUES (?, ?, ?, ?, ?)",
        (raw_text, skills, experience_years, desired_roles, locations),
    )
    await DB.commit()


async def get_user_profile() -> Optional[dict]:
    """Retorna o perfil do usuário ou None."""
    cursor = await DB.execute("SELECT * FROM user_profile LIMIT 1")
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


# --- Vagas notificadas ---

async def is_job_notified(job_id: str) -> bool:
    """Verifica se uma vaga já foi notificada."""
    cursor = await DB.execute(
        "SELECT 1 FROM notified_jobs WHERE id = ?", (job_id,)
    )
    return await cursor.fetchone() is not None


async def mark_job_notified(
    job_id: str, source: str, title: str, company: str, url: str
) -> None:
    """Marca uma vaga como notificada."""
    await DB.execute(
        "INSERT OR IGNORE INTO notified_jobs (id, source, title, company, url) "
        "VALUES (?, ?, ?, ?, ?)",
        (job_id, source, title, company, url),
    )
    await DB.commit()


# --- Log de buscas ---

async def log_search(source: str, jobs_found: int, jobs_matched: int) -> None:
    """Registra uma busca no log."""
    await DB.execute(
        "INSERT INTO search_log (source, jobs_found, jobs_matched) VALUES (?, ?, ?)",
        (source, jobs_found, jobs_matched),
    )
    await DB.commit()


# --- Subscribers (chats que recebem notificações) ---

async def add_subscriber(chat_id: str) -> None:
    """Registra um chat_id para receber notificações."""
    await DB.execute(
        "INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)",
        (str(chat_id),),
    )
    await DB.commit()


async def get_subscribers() -> list[str]:
    """Retorna todos os chat_ids registrados."""
    cursor = await DB.execute("SELECT chat_id FROM subscribers")
    rows = await cursor.fetchall()
    return [row["chat_id"] for row in rows]


# --- Limpeza / expurgo ---

async def purge_old_jobs(retention_days: int = 30) -> int:
    """
    Remove vagas notificadas com mais de X dias.
    Retorna o número de registros excluídos.
    """
    cursor = await DB.execute(
        "DELETE FROM notified_jobs WHERE notified_at < datetime('now', ?)",
        (f"-{retention_days} days",),
    )
    await DB.commit()
    return cursor.rowcount


async def purge_old_logs(retention_days: int = 90) -> int:
    """Remove logs de busca com mais de X dias."""
    cursor = await DB.execute(
        "DELETE FROM search_log WHERE searched_at < datetime('now', ?)",
        (f"-{retention_days} days",),
    )
    await DB.commit()
    return cursor.rowcount