"""
Parsers de currículo.
Extrai texto de PDF e DOCX e faz uma análise simples de skills.
"""
import re
from io import BytesIO
from pathlib import Path

# --- Extração de texto ---


async def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrai texto de um arquivo PDF."""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


async def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extrai texto de um arquivo DOCX."""
    from docx import Document

    doc = Document(BytesIO(file_bytes))
    text_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text.strip())
    return "\n".join(text_parts)


async def extract_text(file_bytes: bytes, filename: str) -> str:
    """Roteia para o extrator correto baseado na extensão."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return await extract_text_from_docx(file_bytes)
    elif ext in (".txt", ".md"):
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Formato não suportado: {ext}. Use PDF, DOCX ou TXT.")


# --- Análise de skills ---

# Conjunto expansível de skills conhecidas
TECH_SKILLS = {
    # Linguagens
    "python", "javascript", "typescript", "java", "kotlin", "swift",
    "go", "golang", "rust", "c++", "c#", "ruby", "php", "scala",
    "elixir", "clojure", "haskell", "dart", "r", "matlab",
    # Frontend
    "react", "angular", "vue", "svelte", "next.js", "nextjs",
    "nuxt", "tailwind", "bootstrap", "css", "html", "sass", "redux",
    # Backend
    "django", "flask", "fastapi", "spring", "spring boot", "node.js",
    "nodejs", "express", "nestjs", "rails", "laravel", ".net",
    "graphql", "rest", "grpc", "websocket",
    # DevOps / Cloud
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "k8s", "terraform", "ansible", "jenkins", "github actions",
    "gitlab ci", "circleci", "prometheus", "grafana", "datadog",
    # Dados
    "sql", "postgresql", "postgres", "mysql", "mongodb", "redis",
    "elasticsearch", "kafka", "rabbitmq", "spark", "airflow",
    "dbt", "snowflake", "bigquery", "power bi",
    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",
    # IA / ML
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "nlp", "computer vision", "llm", "langchain", "openai",
    # Outros
    "git", "linux", "agile", "scrum", "jira", "figma",
    "microservices", "serverless", "rest api", "api",
    "tdd", "ci/cd", "solid", "design patterns",
}


async def extract_skills(text: str) -> list[str]:
    """Varre o texto do currículo e encontra skills conhecidas."""
    text_lower = text.lower()
    found = set()

    for skill in TECH_SKILLS:
        # Busca por palavra inteira ou composta
        pattern = re.escape(skill)
        if re.search(rf"\b{pattern}\b", text_lower):
            found.add(skill)

    # Tenta estimar anos de experiência
    return sorted(found)


async def estimate_experience_years(text: str) -> int:
    """Estima anos de experiência a partir de padrões no texto."""
    # Padrões comuns: "X anos de experiência", "X+ years", "since 2018"
    patterns = [
        r"(\d+)\+?\s*(?:anos|years?)",
        r"(?:desde|since)\s*(\d{4})",
    ]

    import datetime

    # Tenta match de "X anos"
    match = re.search(r"(\d+)\+?\s*(?:anos|years?).*?(?:experiência|experience)", text.lower())
    if match:
        return int(match.group(1))

    # Tenta extrair datas de início
    years_found = re.findall(r"(?:19|20)(\d{2})", text)
    if years_found:
        earliest = min(int(y) for y in years_found)
        if earliest < 50:
            earliest += 2000
        else:
            earliest += 1900
        current_year = datetime.datetime.now().year
        return max(0, current_year - earliest)

    return 0


async def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Pipeline completo: extrai texto → encontra skills → estima experiência.

    Retorna:
        {
            "raw_text": str,
            "skills": list[str],
            "experience_years": int,
        }
    """
    raw_text = await extract_text(file_bytes, filename)
    skills = await extract_skills(raw_text)
    experience_years = await estimate_experience_years(raw_text)

    return {
        "raw_text": raw_text,
        "skills": skills,
        "experience_years": experience_years,
    }