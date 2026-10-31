"""Handlers de comandos do bot."""
from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start — boas-vindas e instruções iniciais."""
    from db import add_subscriber
    await add_subscriber(str(update.effective_chat.id))
    welcome = (
        "👋 *JobsBot — Seu assistente de vagas!*\n\n"
        "Eu busco vagas alinhadas ao seu perfil em diversas fontes "
        "(APIs públicas, GitHub, sites de empresas) e te notifico "
        "quando encontrar algo relevante.\n\n"
        "📎 *Para começar:* envie seu currículo (PDF, DOCX ou TXT) "
        "com o comando /upload ou simplesmente me mande o arquivo.\n\n"
        "🔧 *Comandos disponíveis:*\n"
        "  /start — Esta mensagem\n"
        "  /help — Ajuda detalhada\n"
        "  /profile — Ver seu perfil salvo\n"
        "  /upload — Enviar currículo\n"
        "  /search — Buscar vagas agora\n"
        "  /config — Configurar preferências\n"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help — ajuda detalhada."""
    help_text = (
        "📖 *Como usar o JobsBot*\n\n"
        "1️⃣ Envie seu currículo com /upload\n"
        "2️⃣ O bot extrai automaticamente suas skills\n"
        "3️⃣ Configure cargos e localizações com /config\n"
        "4️⃣ Use /search para buscar vagas na hora\n"
        "5️⃣ O bot também busca automaticamente a cada 12h\n\n"
        "*Fontes de vagas:*\n"
        "• Remotive / Remote OK / Himalayas / We Work Remotely (vagas remotas globais)\n"
        "• Wellfound / GitHub (startups e repositórios de vagas)\n"
        "• Programathor / GeekHunter (vagas BR)\n\n"
        "*Dica:* quanto mais completo seu currículo, melhor o match!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /profile — mostra o perfil salvo do usuário."""
    from db import get_user_profile

    user_profile = await get_user_profile()
    if not user_profile:
        await update.message.reply_text(
            "⚠️ Nenhum perfil salvo ainda. Envie seu currículo com /upload!"
        )
        return

    skills = user_profile.get("skills", "")
    roles = user_profile.get("desired_roles", "Não definido")
    locations = user_profile.get("locations", "Não definido")
    exp = user_profile.get("experience_years", 0)

    profile_text = (
        f"👤 *Seu Perfil*\n\n"
        f"🛠 *Skills:* {skills}\n"
        f"💼 *Cargos:* {roles}\n"
        f"📍 *Localizações:* {locations}\n"
        f"⏳ *Experiência estimada:* {exp} anos\n\n"
        "Use /config para atualizar cargos e localizações.\n"
        "Use /upload para enviar um novo currículo."
    )
    await update.message.reply_text(profile_text, parse_mode="Markdown")


async def search_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /search — busca vagas imediatamente."""
    from db import get_user_profile
    from config import ENABLED_SOURCES, MIN_MATCH_SCORE
    from scrapers import search_all_sources
    from matcher import filter_and_rank

    user_profile = await get_user_profile()
    if not user_profile or not user_profile.get("skills"):
        await update.message.reply_text(
            "⚠️ Envie seu currículo primeiro com /upload para eu saber o que buscar!"
        )
        return

    await update.message.reply_text("🔍 Buscando vagas...isso pode levar alguns segundos.")

    skills = [s.strip() for s in user_profile["skills"].split(",") if s.strip()]
    roles = user_profile.get("desired_roles", "")
    locations = user_profile.get("locations", "")

    results = await search_all_sources(ENABLED_SOURCES, skills, roles, locations)

    # Log por fonte
    source_summary = []
    for src, jobs in results.items():
        source_summary.append(f"{src}: {len(jobs)}")

    total_found = sum(len(jobs) for jobs in results.values())
    if total_found == 0:
        await update.message.reply_text(
            "😔 Nenhuma vaga encontrada agora. Tente novamente mais tarde!"
        )
        return

    # Achata todas as vagas e ranqueia
    all_jobs = []
    for source, jobs in results.items():
        all_jobs.extend(jobs)

    ranked = await filter_and_rank(all_jobs, skills, roles, MIN_MATCH_SCORE, max_results=25)

    if not ranked:
        await update.message.reply_text(
            f"📊 {total_found} vagas encontradas ({', '.join(source_summary)}), "
            f"mas nenhuma com match suficiente "
            f"(mínimo {int(MIN_MATCH_SCORE * 100)}%).\n"
            "Tente ajustar com /config ou enriquecer seu currículo."
        )
        return

    # Mostra resumo
    await update.message.reply_text(
        f"📊 {total_found} vagas encontradas ({', '.join(source_summary)}), "
        f"{len(ranked)} com match ≥ {int(MIN_MATCH_SCORE * 100)}%:"
    )

    # Formata e envia resultados
    for job in ranked:
        score_pct = int(job["match_score"] * 100)
        msg = (
            f"🎯 *{job['title']}* — {score_pct}% match\n"
            f"🏢 {job.get('company', 'N/I')}\n"
            f"📍 {job.get('location', 'N/I')}\n"
            f"🔗 [Ver vaga]({job.get('url', '#')})\n"
            f"📦 Fonte: {job.get('source', 'N/I')}"
        )
        try:
            await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception:
            # Fallback sem Markdown se der erro de parse
            await update.message.reply_text(msg.replace("*", "").replace("[Ver vaga]", "🔗 " + job.get("url", "#")))


async def config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /config — mostra instruções de como configurar."""
    await update.message.reply_text(
        "⚙️ *Configuração*\n\n"
        "Para configurar use:\n"
        "  /setrole Backend Developer, Data Engineer\n"
        "  /setlocation Brasil, Remoto, LATAM\n\n"
        "Use /profile para ver suas configurações atuais.",
        parse_mode="Markdown",
    )


async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Define os cargos desejados."""
    from db import get_user_profile, save_user_profile

    if not context.args:
        await update.message.reply_text(
            "Uso: /setrole Cargo1, Cargo2, Cargo3\n"
            "Exemplo: /setrole Backend Developer, Data Engineer"
        )
        return

    profile = await get_user_profile()
    if not profile:
        await update.message.reply_text("⚠️ Envie seu currículo primeiro com /upload!")
        return

    roles = " ".join(context.args)
    await save_user_profile(
        raw_text=profile["raw_text"],
        skills=profile["skills"],
        experience_years=profile["experience_years"],
        desired_roles=roles,
        locations=profile["locations"],
    )
    await update.message.reply_text(f"✅ Cargos atualizados: {roles}")


async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Define as localizações preferidas."""
    from db import get_user_profile, save_user_profile

    if not context.args:
        await update.message.reply_text(
            "Uso: /setlocation Local1, Local2\n"
            "Exemplo: /setlocation Brasil, Remoto, LATAM, EUA"
        )
        return

    profile = await get_user_profile()
    if not profile:
        await update.message.reply_text("⚠️ Envie seu currículo primeiro com /upload!")
        return

    locations = " ".join(context.args)
    await save_user_profile(
        raw_text=profile["raw_text"],
        skills=profile["skills"],
        experience_years=profile["experience_years"],
        desired_roles=profile["desired_roles"],
        locations=locations,
    )
    await update.message.reply_text(f"✅ Localizações atualizadas: {locations}")