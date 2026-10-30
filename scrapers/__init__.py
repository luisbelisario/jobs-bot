"""Scrapers de vagas — um módulo por fonte."""
from scrapers.remotive import RemotiveScraper
from scrapers.github_jobs import GitHubJobsScraper
from scrapers.programathor import ProgramathorScraper
from scrapers.remoteok import RemoteOKScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.weworkremotely import WeWorkRemotelyScraper
from scrapers.wellfound import WellfoundScraper
from scrapers.geekhunter import GeekHunterScraper

# Registro de scrapers disponíveis
SCRAPERS = {
    "remotive": RemotiveScraper(),
    "github": GitHubJobsScraper(),
    "programathor": ProgramathorScraper(),
    "remoteok": RemoteOKScraper(),
    "himalayas": HimalayasScraper(),
    "weworkremotely": WeWorkRemotelyScraper(),
    "wellfound": WellfoundScraper(),
    "geekhunter": GeekHunterScraper(),
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
            # Log silencioso — não interrompe outras fontes por falha de uma
            print(f"[{source_name}] Erro na busca: {e}")
            results[source_name] = []
    return results