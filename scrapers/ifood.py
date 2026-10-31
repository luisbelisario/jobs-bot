"""
Scraper do iFood — site próprio de carreiras (Next.js).
API: https://carreiras.ifood.com.br/_next/data/{buildId}/pt/jobs.json
Expõe vagas do Greenhouse internamente.
"""
from scrapers.base import BaseScraper

# Build ID do Next.js — pode expirar, precisa ser atualizado periodicamente
# Pegue o atual em: carreiras.ifood.com.br → view-source → procurar "buildId"
BUILD_ID = "YATAhmMVpK4CYCM4Mfmpf"


class IfoodScraper(BaseScraper):
    """Busca vagas do iFood via Next.js API."""

    JOBS_URL = f"https://carreiras.ifood.com.br/_next/data/{BUILD_ID}/pt/jobs.json"

    def __init__(self):
        super().__init__(name="ifood")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        try:
            resp = await client.get(self.JOBS_URL)
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("pageProps", {}).get("jobs", [])

            for job in jobs:
                if not isinstance(job, dict):
                    continue

                job_id = str(job.get("id", job.get("internal_job_id", "")))
                if not job_id or job_id in seen_ids:
                    continue

                title = job.get("title", "")
                location = job.get("location", {}).get("name", "") if isinstance(job.get("location"), dict) else ""
                url = job.get("absolute_url", "")

                # Sem filtro — deixa o matcher de IA decidir relevância
                # (vagas de negócios terão score baixo, tech terá alto)

                seen_ids.add(job_id)
                all_jobs.append({
                    "id": f"ifood-{job_id}",
                    "title": title,
                    "company": "iFood",
                    "location": location,
                    "url": url,
                    "description": title,  # sem descrição na listagem
                    "source": "ifood",
                })

        except Exception as e:
            print(f"[ifood] Erro: {e}")

        return all_jobs