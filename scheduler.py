"""
Agendador de buscas periódicas.
Roda em background, busca vagas e notifica o usuário via Telegram.
Só executa buscas em dias úteis (segunda a sexta).
"""
import asyncio
from datetime import datetime
from config import SEARCH_INTERVAL_HOURS, ENABLED_SOURCES, MIN_MATCH_SCORE, WEEKDAYS_ONLY


def is_weekday() -> bool:
    """Retorna True se hoje for dia útil (seg-sex)."""
    return datetime.now().weekday() < 5  # 0=seg, 4=sex, 5=sab, 6=dom


async def run_scheduled_search(bot) -> None:
    """
    Executa uma rodada completa de busca e notificação.
    Chamada periodicamente pelo JobQueue do PTB.
    Só executa em dias úteis.
    """
    if WEEKDAYS_ONLY and not is_weekday():
        print("[scheduler] Fim de semana — pulando busca.")
        return
    from db import get_user_profile, is_job_notified, mark_job_notified, log_search
    from scrapers import search_all_sources
    from matcher import filter_and_rank
    from config import TELEGRAM_CHAT_ID

    profile = await get_user_profile()
    if not profile or not profile.get("skills"):
        print("[scheduler] Nenhum perfil salvo — pulando busca.")
        return

    skills = [s.strip() for s in profile["skills"].split(",") if s.strip()]
    roles = profile.get("desired_roles", "")
    locations = profile.get("locations", "")

    if not skills:
        return

    print(f"[scheduler] Iniciando busca para {len(skills)} skills...")
    results = await search_all_sources(ENABLED_SOURCES, skills, roles, locations)

    all_jobs = []
    for source, jobs in results.items():
        print(f"[scheduler] {source}: {len(jobs)} vagas encontradas")
        all_jobs.extend(jobs)

    if not all_jobs:
        return

    # Filtra e ranqueia
    ranked = await filter_and_rank(all_jobs, skills, roles, MIN_MATCH_SCORE, max_results=5)

    # Remove vagas já notificadas
    new_jobs = []
    for job in ranked:
        already = await is_job_notified(job["id"])
        if not already:
            new_jobs.append(job)

    if not new_jobs:
        print(f"[scheduler] {len(ranked)} matches, mas todos já notificados.")
        return

    # Notifica cada vaga nova — para todos os subscribers
    from config import TELEGRAM_CHAT_ID
    from db import get_subscribers

    chat_ids: list[str] = []
    env_chat = TELEGRAM_CHAT_ID
    if env_chat:
        chat_ids.append(env_chat)
    # Também notifica todos que já interagiram com o bot
    subscribers = await get_subscribers()
    for sid in subscribers:
        if sid not in chat_ids:
            chat_ids.append(sid)

    if not chat_ids:
        print("[scheduler] Nenhum chat configurado — configure TELEGRAM_CHAT_ID ou interaja com o bot primeiro.")
        return

    for job in new_jobs:
        score_pct = int(job["match_score"] * 100)
        msg = (
            f"🔔 *Nova vaga!* — {score_pct}% match\n\n"
            f"🎯 *{job['title']}*\n"
            f"🏢 {job.get('company', 'N/I')}\n"
            f"📍 {job.get('location', 'N/I')}\n"
            f"🔗 [Ver vaga]({job.get('url', '#')})\n"
            f"📦 Fonte: {job.get('source', 'N/I')}"
        )
        for cid in chat_ids:
            try:
                await bot.send_message(
                    chat_id=cid,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            except Exception as e:
                print(f"[scheduler] Erro ao notificar chat={cid}: {e}")
        await mark_job_notified(
            job_id=job["id"],
            source=job["source"],
            title=job["title"],
            company=job.get("company", ""),
            url=job.get("url", ""),
        )
        # Pequeno delay entre mensagens para não floodar
        await asyncio.sleep(0.5)

    # Log da busca
    for source, jobs in results.items():
        if jobs:
            matched = sum(1 for j in ranked if j["source"] == source)
            await log_search(source, len(jobs), matched)

    print(f"[scheduler] Busca concluída: {len(new_jobs)} vagas novas notificadas.")


def setup_scheduler(application) -> None:
    """
    Configura o JobQueue do PTB para rodar buscas periódicas.
    """
    job_queue = application.job_queue

    # Converte horas para segundos
    interval_seconds = SEARCH_INTERVAL_HOURS * 3600

    async def scheduled_job(context):
        await run_scheduled_search(context.bot)

    # Agenda a primeira execução (após 30s do start) e repete
    job_queue.run_repeating(
        scheduled_job,
        interval=interval_seconds,
        first=30,  # primeira execução 30s após iniciar
        name="job_search",
    )

    # Limpeza diária: expurga vagas >30 dias e logs >90 dias
    async def daily_purge(context):
        from db import purge_old_jobs, purge_old_logs
        deleted_jobs = await purge_old_jobs(30)
        deleted_logs = await purge_old_logs(90)
        if deleted_jobs or deleted_logs:
            print(f"[scheduler] Expurgo: {deleted_jobs} vagas, {deleted_logs} logs removidos.")

    job_queue.run_repeating(
        daily_purge,
        interval=86400,  # 24h
        first=120,  # primeira após 2min do start
        name="daily_purge",
    )

    print(f"[scheduler] Buscas agendadas a cada {SEARCH_INTERVAL_HOURS}h.")