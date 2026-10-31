"""
Scraper da plataforma Greenhouse — usado por iFood, Thoughtworks, Housecall Pro.
API pública: https://boards.greenhouse.io/{company}/jobs (JSON)
"""
from scrapers.base import BaseScraper

EMPRESAS = [
    {"name": "iFood", "board": "ifood", "region": "BR"},
    {"name": "Thoughtworks", "board": "thoughtworks", "region": "BR/LATAM"},
    {"name": "Housecall Pro", "board": "housecallpro", "region": "LATAM/USA"},
]


class GreenhouseScraper(BaseScraper):
    """Busca vagas em boards do Greenhouse."""

    BOARD_URL = "https://boards.greenhouse.io/{board}/jobs"

    def __init__(self):
        super().__init__(name="greenhouse")

    async def search(self, skills: list[str], roles: str, locations: str = "") -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        skills_lower = {s.lower() for s in skills}
        roles_lower = [r.strip().lower() for r in roles.split(",") if r.strip()] if roles else []

        for empresa in EMPRESAS:
            url = self.BOARD_URL.format(board=empresa["board"])
            try:
                resp = await client.get(url, headers={"Accept": "application/json"})
                resp.raise_for_status()
                data = resp.json()
                jobs = data.get("jobs", []) if isinstance(data, dict) else data

                for job in jobs:
                    if not isinstance(job, dict):
                        continue
                    job_id = str(job.get("id", ""))
                    if not job_id or job_id in seen_ids:
                        continue

                    title = job.get("title", "")
                    location = job.get("location", {}).get("name", "") if isinstance(job.get("location"), dict) else ""
                    abs_url = job.get("absolute_url", "")

                    # Filtro básico por skills
                    text = f"{title} {location}".lower()
                    has_skill = any(s in text for s in skills_lower)
                    has_role = any(r in text for r in roles_lower)
                    if not has_skill and not has_role:
                        continue

                    seen_ids.add(job_id)
                    all_jobs.append({
                        "id": f"greenhouse-{job_id}",
                        "title": title,
                        "company": empresa["name"],
                        "location": location or empresa["region"],
                        "url": abs_url,
                        "description": text[:1000],
                        "source": "greenhouse",
                    })

            except Exception as e:
                print(f"[greenhouse] Erro em {empresa['name']}: {e}")
                continue

        return all_jobs