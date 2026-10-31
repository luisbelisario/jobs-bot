#!/usr/bin/env python3
"""
JobsBot — Assistente de busca de vagas via Telegram.

Uso:
    python main.py

Requer TELEGRAM_BOT_TOKEN no arquivo .env.
"""
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, validate
from db import init_db, close_db
from handlers.commands import (
    start,
    help_cmd,
    profile,
    search_now,
    config_cmd,
    set_role,
    set_location,
)
from handlers.resume import upload_resume, handle_document


async def post_init(app: Application) -> None:
    """Inicializa o banco e pré-carrega modelo de IA."""
    await init_db()
    print("✅ Banco de dados inicializado.")

    # Pré-carrega o modelo de embeddings (download único ~80MB)
    try:
        from embeddings import _get_model
        _get_model()
        print("✅ Modelo de IA carregado.")
    except Exception as e:
        print(f"⚠️  Modelo IA indisponível: {e}")
        print("   Usando fallback por palavras-chave.")


async def post_shutdown(app: Application) -> None:
    """Fecha conexões ao parar o bot."""
    await close_db()
    print("🛑 Banco de dados fechado.")


def main() -> None:
    """Inicializa e roda o bot."""
    # Valida configuração
    validate()

    # Cria a aplicação do Telegram
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Registra handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("search", search_now))
    app.add_handler(CommandHandler("config", config_cmd))
    app.add_handler(CommandHandler("setrole", set_role))
    app.add_handler(CommandHandler("setlocation", set_location))
    app.add_handler(CommandHandler("upload", upload_resume))

    # Handler para documentos (currículo)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Inicia o bot (gerencia o event loop internamente)
    print("🤖 JobsBot iniciado! Pressione Ctrl+C para parar.")
    app.run_polling()


if __name__ == "__main__":
    main()