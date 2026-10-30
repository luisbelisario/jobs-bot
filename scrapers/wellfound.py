"""
Scraper do Wellfound (antigo AngelList) — vagas em startups.
Fonte: https://wellfound.com/jobs
Usa scraping da listagem pública com fallback para API.
"""
from scrapers.base import BaseScraper


class WellfoundScraper(BaseScraper):
    """Busca vagas no Wellfound (AngelList)."""

    BASE_URL = "https://wellfound.com"

    def __init__(self):
        super().__init__(name="wellfound")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        roles_list = [r.strip() for r in roles.split(",") if r.strip()] if roles else ["software engineer"]
        locations_list = [l.strip() for l in locations.split(",") if l.strip()] if locations else [""]

        for role in roles_list[:2]:
            for loc in locations_list[:2]:
                params = {"role": role}
                if loc:
                    params["location"] = loc

                try:
                    headers = {
                        "Accept": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    }
                    resp = await client.get(
                        f"{self.BASE_URL}/jobs",
                        params=params,
                        headers=headers,
                    )
                    resp.raise_for_status()

                    # Tenta parse como JSON primeiro
                    try:
                        data = resp.json()
                        jobs = data if isinstance(data, list) else data.get("jobs", data.get("results", []))
                    except Exception:
                        # Fallback: scraping HTML
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(resp.text, "lxml")
                        cards = soup.select("[data-job-id], .job-listing, .job-card, [class*='Job']")
                        jobs = []
                        for card in cards:
                            title_el = card.find(["h2", "h3", "a"])
                            link = card.find("a", href=True)
                            jobs.append({
                                "id": card.get("data-job-id", hash(str(card))),
                                "title": title_el.get_text(strip=True) if title_el else "",
                                "company_name": "",
                                "location_names": ["Remoto"],
                                "url": link["href"] if link else "",
                                "description": card.get_text(strip=True)[:1000],
                            })

                    for job in jobs:
                        if not isinstance(job, dict):
                            continue
                        job_id = str(job.get("id", hash(str(job))))
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        location = job.get("location_names", job.get("location", ["Remoto"]))
                        if isinstance(location, list):
                            location = ", ".join(location)

                        url = job.get("url", "")
                        if url and not url.startswith("http"):
                            url = f"{self.BASE_URL}{url}"

                        all_jobs.append({
                            "id": f"wellfound-{job_id}",
                            "title": job.get("title", ""),
                            "company": job.get("company_name", job.get("company", "")),
                            "location": location,
                            "url": url,
                            "description": (job.get("description", "") or "")[:2000],
                            "source": "wellfound",
                        })

                except Exception as e:
                    print(f"[wellfound] Erro na busca role={role} loc={loc}: {e}")
                    continue

        return all_jobs