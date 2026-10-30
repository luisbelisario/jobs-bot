"""
Scraper de repositórios GitHub que agregam vagas.
Fontes:
- github.com/backend-br/vagas (vagas de backend no Brasil)
- github.com/frontendbr/vagas (vagas de frontend no Brasil)
- github.com/remoteintech/remote-jobs (vagas remotas globais)

Usa a API pública do GitHub (60 req/h sem token, 5000 com token).
"""
from scrapers.base import BaseScraper

# Repositórios de vagas em Markdown
VAGAS_REPOS = [
    {
        "owner": "backend-br",
        "repo": "vagas",
        "path": "README.md",
        "region": "BR",
        "category": "backend",
    },
    {
        "owner": "frontendbr",
        "repo": "vagas",
        "path": "README.md",
        "region": "BR",
        "category": "frontend",
    },
    {
        "owner": "remoteintech",
        "repo": "remote-jobs",
        "path": "README.md",
        "region": "Global",
        "category": "remote",
    },
]


class GitHubJobsScraper(BaseScraper):
    """Busca vagas em repositórios curados do GitHub."""

    GITHUB_API = "https://api.github.com"

    def __init__(self):
        super().__init__(name="github")

    async def _fetch_readme(self, client, owner: str, repo: str, path: str) -> str:
        """Baixa o conteúdo de um arquivo via GitHub API."""
        url = f"{self.GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        resp = await client.get(url, headers={"Accept": "application/vnd.github.v3.raw"})
        resp.raise_for_status()
        return resp.text

    def _parse_markdown_vagas(self, md_text: str) -> list[dict]:
        """Extrai vagas de um README.md no formato típico de repo de vagas."""
        import re

        jobs = []
        # Padrão: linhas que parecem vagas (contêm links, tags de remoto/presencial, etc.)
        lines = md_text.split("\n")
        current_section = ""

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                if line.startswith("##"):
                    current_section = line.replace("#", "").strip()
                continue

            # Procura links markdown [texto](url) que parecem vagas
            link_match = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", line)
            for title, url in link_match:
                # Filtra links que não são vagas (ex: site do repo, badges)
                if any(skip in url.lower() for skip in (
                    "github.com/user", "linkedin.com", "badge", "travis",
                    "circleci", "contributor", "license",
                )):
                    continue

                # Extrai informações da linha
                company = ""
                location = ""

                # Tenta extrair empresa e localização
                remaining = line.replace(f"[{title}]({url})", "").strip(" -–|")
                parts = [p.strip() for p in remaining.split("·") if p.strip()]
                if not parts:
                    parts = [p.strip() for p in remaining.split("-") if p.strip()]
                if not parts:
                    parts = [p.strip() for p in remaining.split("|") if p.strip()]

                if parts:
                    company = parts[0].strip(" @")
                    if len(parts) > 1:
                        location = parts[1].strip()

                job_id = f"github-{hash(url) & 0x7FFFFFFF:x}"

                jobs.append({
                    "id": job_id,
                    "title": title.strip(),
                    "company": company,
                    "location": location or current_section or "Não especificado",
                    "url": url,
                    "description": line[:1000],
                    "source": "github",
                })

        return jobs

    async def search(
        self, skills: list[str], roles: str, locations: str = ""
    ) -> list[dict]:
        client = await self._get_client()
        all_jobs = []
        seen_ids = set()

        for repo in VAGAS_REPOS:
            try:
                md_text = await self._fetch_readme(
                    client, repo["owner"], repo["repo"], repo["path"]
                )
                jobs = self._parse_markdown_vagas(md_text)
                for job in jobs:
                    if job["id"] not in seen_ids:
                        seen_ids.add(job["id"])
                        job["region"] = repo["region"]
                        all_jobs.append(job)
            except Exception as e:
                print(f"[github] Erro ao buscar {repo['owner']}/{repo['repo']}: {e}")
                continue

        return all_jobs