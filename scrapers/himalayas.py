"""
Scraper da API do Himalayas — vagas remotas globais.
API: https://himalayas.app/jobs/api
"""
from scrapers.base import BaseScraper


class HimalayasScraper(BaseScraper):
    """Busca vagas remotas via Himalayas API."""

    BASE_URL = "https://himalayas.app/jobs/api"

    def __init__(self):
        super().__init__(name="himalayas")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        # Busca paginada (até 3 páginas)
        for page in range(1, 4):
            params = {"page": page, "limit": 50}
            if skills:
                params["search"] = skills[0]

            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                jobs = data.get("jobs", data) if isinstance(data, dict) else data

                if not jobs:
                    break

                for job in jobs:
                    if not isinstance(job, dict):
                        continue
                    job_id = str(job.get("id", hash(str(job))))
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    all_jobs.append({
                        "id": f"himalayas-{job_id}",
                        "title": job.get("title", ""),
                        "company": job.get("company_name", job.get("company", "")),
                        "location": job.get("location", "Remoto"),
                        "url": job.get("application_url", job.get("url", "")),
                        "description": (job.get("description", "") or "")[:2000],
                        "source": "himalayas",
                    })
            except Exception as e:
                print(f"[himalayas] Erro na página {page}: {e}")
                break

        return all_jobs