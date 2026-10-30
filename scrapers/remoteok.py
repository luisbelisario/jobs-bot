"""
Scraper da API pública do Remote OK — vagas remotas globais.
API: https://remoteok.com/api
Gratuita, sem autenticação, ~15-20k vagas remotas ativas.
"""
from scrapers.base import BaseScraper


class RemoteOKScraper(BaseScraper):
    """Busca vagas remotas via Remote OK API."""

    BASE_URL = "https://remoteok.com/api"

    def __init__(self):
        super().__init__(name="remoteok")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        try:
            headers = {"Accept": "application/json"}
            resp = await client.get(self.BASE_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            # O primeiro elemento da resposta é metadados (legal notice),
            # os demais são vagas
            jobs = data[1:] if len(data) > 1 else data

            for job in jobs:
                job_id = str(job.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = job.get("position", "")
                company = job.get("company", "")
                description = job.get("description", "") or ""
                tags = job.get("tags", [])
                url = job.get("url", "")
                location = job.get("location", "Remoto")

                # Filtro leve: verifica se alguma skill ou role aparece
                # nos campos relevantes (evita trazer tudo sem critério)
                search_text = f"{title} {company} {' '.join(tags)}".lower()
                has_match = any(
                    s.lower() in search_text for s in skills
                )
                if roles:
                    roles_lower = [r.strip().lower() for r in roles.split(",") if r.strip()]
                    has_match = has_match or any(
                        r in search_text for r in roles_lower
                    )

                if not has_match and skills:
                    continue  # skip — não tem nenhuma skill relevante

                all_jobs.append({
                    "id": f"remoteok-{job_id}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url if url else f"https://remoteok.com/remote-jobs/{job_id}",
                    "description": (description[:2000] if description else ""),
                    "source": "remoteok",
                    "tags": ", ".join(tags) if tags else "",
                })

        except Exception as e:
            print(f"[remoteok] Erro na busca: {e}")

        return all_jobs