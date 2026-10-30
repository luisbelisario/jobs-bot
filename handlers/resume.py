"""Handler de upload e processamento de currículo."""
from telegram import Update
from telegram.ext import ContextTypes

from db import save_user_profile, get_user_profile
from resume_parser import parse_resume


async def upload_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /upload — instrui o usuário a enviar o arquivo."""
    await update.message.reply_text(
        "📎 Me envie seu currículo como arquivo (PDF, DOCX ou TXT) "
        "e eu extrairei suas skills automaticamente!"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa qualquer documento enviado pelo usuário como currículo."""
    document = update.message.document

    if not document:
        # Pode ser uma foto ou outro tipo
        await update.message.reply_text(
            "⚠️ Por favor, envie o currículo como *arquivo* (PDF, DOCX ou TXT), "
            "não como foto.",
            parse_mode="Markdown",
        )
        return

    filename = document.file_name or "resume.pdf"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext not in ("pdf", "docx", "doc", "txt", "md"):
        await update.message.reply_text(
            f"⚠️ Formato *.{ext}* não suportado. Envie PDF, DOCX ou TXT.",
            parse_mode="Markdown",
        )
        return

    # Feedback de progresso
    status_msg = await update.message.reply_text("📄 Lendo seu currículo...")

    # Registra o chat para notificações futuras
    from db import add_subscriber
    await add_subscriber(str(update.effective_chat.id))

    try:
        # Baixa o arquivo do Telegram
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()

        # Parse do currículo
        result = await parse_resume(bytes(file_bytes), filename)

        skills_str = ", ".join(result["skills"]) if result["skills"] else "Nenhuma skill detectada"

        # Mostra o que foi extraído
        summary = (
            f"✅ *Currículo processado!*\n\n"
            f"🛠 *Skills detectadas:* {skills_str}\n"
            f"⏳ *Experiência estimada:* {result['experience_years']} anos\n\n"
        )

        # Tenta carregar perfil existente para preservar roles/locations
        existing = await get_user_profile()
        existing_roles = existing["desired_roles"] if existing else ""
        existing_locations = existing["locations"] if existing else ""

        # Salva no banco
        await save_user_profile(
            raw_text=result["raw_text"],
            skills=skills_str,
            experience_years=result["experience_years"],
            desired_roles=existing_roles,
            locations=existing_locations,
        )

        # Gera embedding do perfil para matching semântico
        from matcher import set_profile
        await set_profile(skills_str, existing_roles, result["raw_text"][:800])

        if not existing_roles:
            summary += (
                "💡 *Próximo passo:* configure os cargos que você busca:\n"
                "  /setrole Backend Developer, Data Engineer\n"
                "E localizações:\n"
                "  /setlocation Brasil, Remoto, LATAM"
            )
        else:
            summary += "Pronto! Use /search para buscar vagas agora."

        await status_msg.edit_text(summary, parse_mode="Markdown")

    except ValueError as e:
        await status_msg.edit_text(f"❌ {e}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Erro ao processar currículo: {e}")