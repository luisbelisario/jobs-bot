"""
Scraper do We Work Remotely — vagas remotas globais.
Fonte: https://weworkremotely.com/
Usa scraping da listagem pública.
"""
from scrapers.base import BaseScraper
from bs4 import BeautifulSoup


class WeWorkRemotelyScraper(BaseScraper):
    """Busca vagas no We Work Remotely."""

    BASE_URL = "https://weworkremotely.com"

    CATEGORIES = {
        "backend": "/categories/remote-back-end-programming-jobs",
        "frontend": "/categories/remote-front-end-programming-jobs",
        "devops": "/categories/remote-devops-sysadmin-jobs",
        "fullstack": "/categories/remote-full-stack-programming-jobs",
        "data": "/categories/remote-data-science-jobs",
    }

    def __init__(self):
        super().__init__(name="weworkremotely")

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        # Determina categorias relevantes baseado nas skills
        skills_lower = {s.lower() for s in skills}
        categories_to_search = []

        if skills_lower & {"python", "java", "go", "rust", "ruby", "php", "c#", "node", "django", "spring", "rails", "laravel", "express", "fastapi", "flask"}:
            categories_to_search.append("backend")
        if skills_lower & {"react", "vue", "angular", "svelte", "javascript", "typescript", "css", "html", "tailwind"}:
            categories_to_search.append("frontend")
        if skills_lower & {"docker", "kubernetes", "aws", "terraform", "jenkins", "ci/cd", "linux"}:
            categories_to_search.append("devops")
        if skills_lower & {"fullstack", "full-stack"}:
            categories_to_search.append("fullstack")

        if not categories_to_search:
            categories_to_search = ["backend", "fullstack"]  # default

        for cat in categories_to_search[:3]:
            url = f"{self.BASE_URL}{self.CATEGORIES.get(cat, self.CATEGORIES['backend'])}"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                # Estrutura do WWR: sections com class "jobs"
                sections = soup.select("section.jobs, .job-listing, li.feature, article")
                if not sections:
                    sections = soup.find_all("li", class_=lambda c: c and "feature" in c)

                for section in sections:
                    try:
                        link = section.find("a", href=True)
                        if not link:
                            continue
                        title_el = section.find(["h4", "h3", "span", "a"])
                        company_el = section.find(class_=lambda c: c and "company" in c.lower()) if hasattr(section, "find") else None
                        location_el = section.find(class_=lambda c: c and "region" in c.lower()) if hasattr(section, "find") else None

                        title = title_el.get_text(strip=True) if title_el else ""
                        company = company_el.get_text(strip=True) if company_el else ""
                        location = location_el.get_text(strip=True) if location_el else "Remoto"
                        url = link["href"]
                        if not url.startswith("http"):
                            url = f"{self.BASE_URL}{url}"

                        job_id = f"wwr-{hash(url) & 0x7FFFFFFF:x}"
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        all_jobs.append({
                            "id": job_id,
                            "title": title,
                            "company": company or "Não informado",
                            "location": location,
                            "url": url,
                            "description": section.get_text(strip=True)[:1500],
                            "source": "weworkremotely",
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"[weworkremotely] Erro na categoria {cat}: {e}")
                continue

        return all_jobs