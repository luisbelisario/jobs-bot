"""
Scraper do GeekHunter — vagas para devs no Brasil.
Fonte: https://geekhunter.com.br/vagas
"""
from scrapers.base import BaseScraper
from bs4 import BeautifulSoup


class GeekHunterScraper(BaseScraper):
    """Busca vagas no GeekHunter (Brasil)."""

    BASE_URL = "https://www.geekhunter.com.br/vagas"

    def __init__(self):
        super().__init__(name="geekhunter")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        # Tenta buscar com parâmetros de skills
        for skill in skills[:3]:
            params = {"search": skill, "page": 1}
            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
            except Exception as e:
                print(f"[geekhunter] Erro ao buscar skill '{skill}': {e}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # Seletores comuns para listagem de vagas
            cards = soup.select(
                ".job-card, .vacancy-card, .opportunity-item, "
                "[class*='job'], [class*='vaga'], [class*='vacancy'], "
                "li[class*='item']"
            )
            if not cards:
                # Tenta qualquer div com link e título
                cards = soup.find_all("div", class_=lambda c: c and any(
                    kw in c.lower() for kw in ["job", "vaga", "vacancy", "card", "item"]
                ))

            for card in cards:
                try:
                    link = card.find("a", href=True)
                    if not link:
                        continue

                    title_el = card.find(["h2", "h3", "h4", "strong"]) or link
                    title = title_el.get_text(strip=True)

                    company_el = card.find(class_=lambda c: c and any(
                        kw in (c or "").lower() for kw in ["company", "empresa", "business"]
                    ))
                    company = company_el.get_text(strip=True) if company_el else ""

                    location_el = card.find(class_=lambda c: c and any(
                        kw in (c or "").lower() for kw in ["location", "local", "city", "remote"]
                    ))
                    location = location_el.get_text(strip=True) if location_el else "Brasil"

                    url = link["href"]
                    if not url.startswith("http"):
                        if url.startswith("/"):
                            url = f"https://www.geekhunter.com.br{url}"
                        else:
                            url = f"https://www.geekhunter.com.br/{url}"

                    job_id = f"geekhunter-{hash(url) & 0x7FFFFFFF:x}"
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    all_jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company or "Não informado",
                        "location": location,
                        "url": url,
                        "description": card.get_text(strip=True)[:1500],
                        "source": "geekhunter",
                    })
                except Exception:
                    continue

        return all_jobs