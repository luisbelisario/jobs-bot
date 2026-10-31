"""
Scraper da plataforma Gupy — usado por Nava, Stefanini, BRQ.
API interna: https://{company}.gupy.io/api/v1/jobs (JSON)
"""
from scrapers.base import BaseScraper

EMPRESAS = [
    {"name": "Nava", "slug": "nava", "region": "BR"},
    {"name": "Stefanini", "slug": "stefanini", "region": "BR"},
    {"name": "BRQ", "slug": "brq", "region": "BR"},
]


class GupyScraper(BaseScraper):
    """Busca vagas em boards do Gupy."""

    API_URL = "https://{slug}.gupy.io/api/v1/jobs"

    def __init__(self):
        super().__init__(name="gupy")

    async def search(self, skills: list[str], roles: str, locations: str = "") -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        skills_lower = {s.lower() for s in skills}
        roles_lower = [r.strip().lower() for r in roles.split(",") if r.strip()] if roles else []

        for empresa in EMPRESAS:
            url = self.API_URL.format(slug=empresa["slug"])
            try:
                params = {"limit": 50, "offset": 0}
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                jobs = data.get("results", data.get("data", [])) if isinstance(data, dict) else data

                for job in jobs:
                    if not isinstance(job, dict):
                        continue
                    job_id = str(job.get("id", ""))
                    if not job_id or job_id in seen_ids:
                        continue

                    title = job.get("name", job.get("title", ""))
                    text_full = f"{title} {job.get('description', '')}"[:800]

                    # Filtro
                    text_lower = text_full.lower()
                    has_skill = any(s in text_lower for s in skills_lower)
                    has_role = any(r in text_lower for r in roles_lower)
                    if not has_skill and not has_role:
                        continue

                    seen_ids.add(job_id)
                    all_jobs.append({
                        "id": f"gupy-{job_id}",
                        "title": title,
                        "company": empresa["name"],
                        "location": job.get("location", job.get("city", empresa["region"])),
                        "url": job.get("url", job.get("externalLink", f"https://{empresa['slug']}.gupy.io/jobs/{job_id}")),
                        "description": text_full[:1500],
                        "source": "gupy",
                    })

            except Exception as e:
                print(f"[gupy] Erro em {empresa['name']}: {e}")
                continue

        return all_jobs