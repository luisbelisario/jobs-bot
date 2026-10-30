"""
Scraper do Programathor — site brasileiro de vagas para desenvolvedores.
URL: https://programathor.com.br/jobs

Faz scraping da listagem pública (sem necessidade de login).
"""
from scrapers.base import BaseScraper
from bs4 import BeautifulSoup


class ProgramathorScraper(BaseScraper):
    """Busca vagas no Programathor (Brasil)."""

    BASE_URL = "https://programathor.com.br/jobs"

    def __init__(self):
        super().__init__(name="programathor")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        # Busca paginada — tenta até 3 páginas
        for page in range(1, 4):
            params = {"page": page}
            # Adiciona skills como filtro de busca
            if skills:
                params["search"] = skills[0]  # Filtro principal pela primeira skill

            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
            except Exception as e:
                print(f"[programathor] Erro na página {page}: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select(".cell-list .job-item, .job-list .cell, [class*='job']")

            if not cards:
                # Tenta seletores alternativos
                cards = soup.find_all("div", class_=lambda c: c and "job" in c.lower())

            if not cards:
                break  # Sem mais resultados

            for card in cards:
                try:
                    # Tenta extrair link e título
                    link_el = card.find("a", href=True)
                    if not link_el:
                        continue

                    title_el = card.find(["h2", "h3", "h4"]) or link_el
                    title = title_el.get_text(strip=True)

                    company_el = card.find(class_=lambda c: c and "company" in c.lower()) if hasattr(card, "find") else None
                    company = company_el.get_text(strip=True) if company_el else ""

                    location_el = card.find(class_=lambda c: c and "location" in c.lower()) if hasattr(card, "find") else None
                    location = location_el.get_text(strip=True) if location_el else "Brasil"

                    url = link_el["href"]
                    if not url.startswith("http"):
                        url = f"https://programathor.com.br{url}"

                    job_id = f"programathor-{hash(url) & 0x7FFFFFFF:x}"

                    if job_id not in seen_ids:
                        seen_ids.add(job_id)
                        all_jobs.append({
                            "id": job_id,
                            "title": title,
                            "company": company or "Não informado",
                            "location": location,
                            "url": url,
                            "description": card.get_text(strip=True)[:1500],
                            "source": "programathor",
                        })
                except Exception as e:
                    print(f"[programathor] Erro ao parse card: {e}")
                    continue

        return all_jobs