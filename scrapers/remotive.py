"""
Scraper da API pública do Remotive — vagas remotas.
API: https://remotive.com/api/remote-jobs
Gratuita, sem autenticação, ~30k vagas remotas.
"""
from scrapers.base import BaseScraper


class RemotiveScraper(BaseScraper):
    """Busca vagas remotas via Remotive API."""

    BASE_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self):
        super().__init__(name="remotive")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()

        # Remotive permite buscar por termo (search) e categoria
        # Vamos usar as skills como termo de busca
        all_jobs = []
        seen_ids = set()

        # Busca por cada skill relevante (limitado a 3 skills para não floodar)
        for skill in skills[:5]:
            params = {"search": skill, "limit": 25}
            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                for job in data.get("jobs", []):
                    job_id = str(job.get("id"))
                    if job_id not in seen_ids:
                        seen_ids.add(job_id)
                        all_jobs.append({
                            "id": f"remotive-{job_id}",
                            "title": job.get("title", ""),
                            "company": job.get("company_name", ""),
                            "location": job.get("candidate_required_location", "Remoto"),
                            "url": job.get("url", ""),
                            "description": (job.get("description", "") or "")[:2000],
                            "source": "remotive",
                            "tags": ", ".join(job.get("tags", [])),
                        })
            except Exception as e:
                print(f"[remotive] Erro ao buscar skill '{skill}': {e}")
                continue

        return all_jobs