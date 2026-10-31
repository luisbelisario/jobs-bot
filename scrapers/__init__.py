"""Scrapers de vagas — um módulo por fonte."""
from scrapers.remoteok import RemoteOKScraper
from scrapers.lever import LeverScraper
from scrapers.ifood import IfoodScraper

# Registro de scrapers disponíveis
SCRAPERS = {
    "remoteok": RemoteOKScraper(),
    "lever": LeverScraper(),
    "ifood": IfoodScraper(),
}


async def search_all_sources(
    enabled_sources: list[str],
    skills: list[str],
    roles: str,
    locations: str = "",
) -> dict[str, list[dict]]:
    """
    Executa todos os scrapers habilitados e retorna {fonte: [vagas]}.
    """
    results = {}
    for source_name in enabled_sources:
        source_name = source_name.strip()
        if source_name not in SCRAPERS:
            continue
        scraper = SCRAPERS[source_name]
        try:
            jobs = await scraper.search(skills=skills, roles=roles, locations=locations)
            results[source_name] = jobs
        except Exception as e:
            print(f"[{source_name}] Erro na busca: {e}")
            results[source_name] = []
    return results