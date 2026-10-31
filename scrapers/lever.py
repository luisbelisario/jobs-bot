"""
Scraper da plataforma Lever — usado por CI&T, Coderio.
Faz scraping do HTML (mais confiável que API JSON).
URL: https://jobs.lever.co/{slug}
"""
from scrapers.base import BaseScraper
from bs4 import BeautifulSoup

EMPRESAS = [
    {"name": "CI&T", "slug": "ciandt", "region": "BR"},
    {"name": "Coderio", "slug": "coderio", "region": "LATAM"},
]


class LeverScraper(BaseScraper):
    """Busca vagas em boards do Lever via scraping HTML."""

    BASE_URL = "https://jobs.lever.co/{slug}"

    def __init__(self):
        super().__init__(name="lever")

    async def search(self, skills: list[str], roles: str, locations: str = "") -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        skills_lower = {s.lower() for s in skills}

        for empresa in EMPRESAS:
            url = self.BASE_URL.format(slug=empresa["slug"])
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Lever: cada vaga é um div.posting com data-qa-posting-id
                postings = soup.select("div.posting[data-qa-posting-id]")
                if not postings:
                    postings = soup.select(".posting")

                for post in postings:
                    posting_id = post.get("data-qa-posting-id", "")
                    if not posting_id or posting_id in seen_ids:
                        continue

                    # Título: h5[data-qa="posting-name"]
                    title_el = post.select_one('h5[data-qa="posting-name"]')
                    if not title_el:
                        title_el = post.find("h5")
                    title = title_el.get_text(strip=True) if title_el else ""

                    # Link
                    link = post.find("a", class_="posting-title")
                    if not link:
                        link = post.find("a", href=True)
                    job_url = link["href"] if link and link.get("href") else ""
                    if job_url and not job_url.startswith("http"):
                        job_url = f"https://jobs.lever.co{job_url}"

                    # Categorias (location, commitment, workplace)
                    location_el = post.select_one(".location")
                    commitment_el = post.select_one(".commitment")
                    workplace_el = post.select_one(".workplaceTypes")
                    location = location_el.get_text(strip=True) if location_el else empresa["region"]
                    commitment = commitment_el.get_text(strip=True) if commitment_el else ""

                    # Filtro por skills
                    text = f"{title} {location} {commitment}".lower()
                    if not any(s in text for s in skills_lower):
                        continue

                    seen_ids.add(posting_id)
                    all_jobs.append({
                        "id": f"lever-{posting_id}",
                        "title": title,
                        "company": empresa["name"],
                        "location": location,
                        "url": job_url,
                        "description": post.get_text(strip=True)[:1500],
                        "source": "lever",
                    })

            except Exception as e:
                print(f"[lever] Erro em {empresa['name']}: {e}")
                continue

        return all_jobs