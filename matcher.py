"""
Motor de matching semântico — usa embeddings + similaridade de cosseno.
Substitui o match binário por compreensão contextual de IA.
"""
import re

# Cache do embedding do perfil (gerado uma vez, reutilizado nas buscas)
_profile_embedding = None
_profile_skills_text = ""


async def set_profile(skills: str, roles: str, resume_text: str = "") -> None:
    """
    Gera e armazena o embedding do perfil do usuário.
    Chamado após upload/envio de currículo.
    """
    global _profile_embedding, _profile_skills_text
    from embeddings import profile_embedding
    _profile_embedding = await profile_embedding(skills, roles, resume_text)
    _profile_skills_text = skills


async def compute_match_score(
    job_title: str,
    job_description: str,
    user_skills: list[str],
    user_desired_roles: str = "",
) -> float:
    """
    Score semântico: similaridade de cosseno (85%) + senioridade (15%).
    """
    global _profile_embedding

    from embeddings import job_embedding, cosine_similarity

    # 1. Similaridade semântica (85%)
    if _profile_embedding is not None:
        job_emb = await job_embedding(job_title, job_description)
        semantic = await cosine_similarity(_profile_embedding, job_emb)
    else:
        # Fallback: sem embedding, usa match simples de palavras
        text = (job_title + " " + job_description).lower()
        skills_lower = {s.lower() for s in user_skills}
        words = set(re.findall(r"\b\w+\b", text))
        found = skills_lower & words
        semantic = min(len(found) * 0.08, 0.85)

    # 2. Senioridade (15%)
    text = (job_title + " " + job_description).lower()
    seniority = 0.0
    seniority_kw = {
        "senior": 0.15, "sênior": 0.15, "sr.": 0.15,
        "lead": 0.15, "staff": 0.15, "principal": 0.15,
        "pleno": 0.08, "mid": 0.08,
    }
    for kw, bonus in seniority_kw.items():
        if kw in text:
            seniority = max(seniority, bonus)

    final = semantic * 0.85 + seniority
    return round(min(final, 1.0), 2)

    # Penalidade para vagas de altíssima senioridade (architect, principal, staff, 8+ years)
    over_seniority_kw = {
        "architect", "principal engineer", "staff engineer", "director",
        "head of engineering", "vp of", "8+ years", "10+ years",
        "15+ years", "distinguished", "fellow",
    }
    text_lower = (job_title + " " + job_description).lower()
    if any(kw in text_lower for kw in over_seniority_kw):
        final *= 0.80  # reduz 20%

    return round(min(final, 1.0), 2)


async def filter_and_rank(
    jobs: list[dict],
    user_skills: list[str],
    user_desired_roles: str = "",
    min_score: float = 0.3,
    max_results: int = 10,
) -> list[dict]:
    """
    Filtra e ordena vagas por relevância semântica.
    Exige que a vaga mencione pelo menos 1 skill técnica explícita.
    """
    scored = []
    skills_lower = {s.lower() for s in user_skills}

    for job in jobs:
        title = job.get("title", "")
        desc = job.get("description", "")

        # Filtro híbrido: precisa ter pelo menos 1 skill CORE (não periférica como "api" ou "git")
        text = f"{title} {desc}".lower()
        words = set(re.findall(r"\b\w+\b", text))
        core_skills = {"java", "python", "aws", "kubernetes", "terraform", "kafka",
                       "docker", "spring", "quarkus", "golang", "kotlin"}
        has_core_skill = bool(skills_lower & words & core_skills)
        if not has_core_skill:
            continue

        # Exclui vagas fullstack/frontend/data pelo título
        title_lower = title.lower()
        excluded = {
            "fullstack", "full-stack", "frontend", "front-end",
            "react developer", "angular developer", "vue developer",
            "data engineer", "data architect", "data scientist", "data analyst",
        }
        if any(ex in title_lower for ex in excluded):
            continue

        score = await compute_match_score(
            job_title=title,
            job_description=desc,
            user_skills=user_skills,
            user_desired_roles=user_desired_roles,
        )
        if score >= min_score:
            job["match_score"] = score
            scored.append(job)

    scored.sort(key=lambda j: j["match_score"], reverse=True)
    return scored[:max_results]