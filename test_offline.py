#!/usr/bin/env python3
"""
Teste offline do JobsBot — valida toda a lógica de negócio sem rede.
Não precisa de token do Telegram nem de acesso à internet.
"""
import sys
import asyncio
import os
import tempfile
from pathlib import Path

# Garante que o diretório do projeto está no path
sys.path.insert(0, str(Path(__file__).resolve().parent))

TESTS_PASSED = 0
TESTS_FAILED = 0


def check(description: str, condition: bool):
    global TESTS_PASSED, TESTS_FAILED
    if condition:
        TESTS_PASSED += 1
        print(f"  ✅ {description}")
    else:
        TESTS_FAILED += 1
        print(f"  ❌ {description}")


# ── Mock de currículo ──────────────────────────────────────────

SAMPLE_RESUME_TXT = """
LUIS SANTOS
Backend Developer | Python Specialist

EXPERIENCE
Senior Backend Developer — Empresa X (2020 - Present)
- Developed microservices using Python, FastAPI, and Django
- Deployed on AWS using Docker, Kubernetes, and Terraform
- Worked with PostgreSQL, Redis, Kafka, and Elasticsearch
- Built CI/CD pipelines with GitHub Actions and GitLab CI
- Implemented monitoring with Prometheus and Grafana
- 6+ years of professional experience

Mid-Level Developer — Empresa Y (2018 - 2020)
- Built REST APIs with Flask and Node.js
- Used MongoDB, MySQL, and Redis
- Frontend with React, TypeScript, and Tailwind

EDUCATION
Computer Science — Universidade Federal (2014 - 2018)

SKILLS
Python, Go, JavaScript, TypeScript, Rust
Django, FastAPI, Flask, Express
AWS, GCP, Docker, Kubernetes, Terraform
PostgreSQL, MongoDB, Redis, Kafka, Elasticsearch
React, Next.js, Tailwind
Git, Linux, CI/CD, TDD
"""


# ── Testes ──────────────────────────────────────────────────────

async def test_resume_parser():
    """Testa extração de skills e experiência."""
    print("\n📄 [1/5] Resume Parser")
    from resume_parser import extract_skills, estimate_experience_years
    import tempfile, os

    # Testa extração de skills
    skills = await extract_skills(SAMPLE_RESUME_TXT)
    check("Detectou Python", "python" in skills)
    check("Detectou Django", "django" in skills)
    check("Detectou AWS", "aws" in skills)
    check("Detectou Docker", "docker" in skills)
    check("Detectou Kubernetes", "kubernetes" in skills)
    check("Detectou PostgreSQL", "postgresql" in skills)
    check("Detectou Kafka", "kafka" in skills)
    check("Detectou React", "react" in skills)
    check("Detectou Go", "go" in skills)
    check("Detectou Rust", "rust" in skills)
    check("Múltiplas skills (>20)", len(skills) >= 20)

    # Testa estimativa de experiência
    exp = await estimate_experience_years(SAMPLE_RESUME_TXT)
    check(f"Experiência detectada ({exp} anos)", exp >= 5)

    # Testa parsing de TXT
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(SAMPLE_RESUME_TXT.encode())
        f.flush()
        from resume_parser import parse_resume
        result = await parse_resume(open(f.name, "rb").read(), "resume.txt")
        os.unlink(f.name)

    check("Parse TXT retornou skills", len(result["skills"]) > 0)
    check("Parse TXT retornou experiência", result["experience_years"] > 0)
    check("Parse TXT retornou raw_text", len(result["raw_text"]) > 100)


async def test_matcher():
    """Testa o algoritmo de match."""
    print("\n🎯 [2/5] Matcher")
    from matcher import compute_match_score, filter_and_rank

    skills = ["python", "django", "aws", "docker", "kubernetes", "postgresql"]

    # Teste 1: match alto
    s1 = await compute_match_score(
        "Senior Python Backend Developer",
        "Looking for python, django, aws, docker, kubernetes. Must know PostgreSQL.",
        skills,
        "Backend Developer",
    )
    check(f"Match alto ({s1}) > 0.7", s1 > 0.7)

    # Teste 2: match baixo (nada em comum)
    s2 = await compute_match_score(
        "UX Designer",
        "Figma, Sketch, user research, design systems",
        skills,
        "Backend Developer",
    )
    check(f"Match baixo ({s2}) < 0.15", s2 < 0.15)

    # Teste 3: skill composta
    s3 = await compute_match_score(
        "Spring Boot Developer",
        "Spring Boot, Java, microservices",
        ["spring boot", "java", "kotlin"],
        "",
    )
    check(f"Skill composta ({s3}) > 0.10", s3 > 0.10)

    # Teste 4: bônus de senioridade
    s4 = await compute_match_score(
        "Staff Python Engineer",
        "Python, backend systems",
        ["python", "aws"],
        "",
    )
    s5 = await compute_match_score(
        "Junior Python Developer",
        "Python, backend systems",
        ["python", "aws"],
        "",
    )
    check(f"Staff ({s4}) > Junior ({s5})", s4 > s5)

    # Teste 5: filter and rank
    jobs = [
        {"id": "1", "title": "Python Dev", "description": "python django aws docker", "source": "test"},
        {"id": "2", "title": "UX Designer", "description": "figma design", "source": "test"},
        {"id": "3", "title": "DevOps Engineer", "description": "docker kubernetes aws terraform", "source": "test"},
        {"id": "4", "title": "Python Backend", "description": "python fastapi aws postgres", "source": "test"},
    ]
    ranked = await filter_and_rank(jobs, skills, "Backend", min_score=0.0)
    check(f"Ranking funciona ({len(ranked)} vagas)", len(ranked) == 4)
    # A primeira deve ser a de maior match
    check("Ordenação correta", ranked[0]["match_score"] >= ranked[-1]["match_score"])


async def test_database():
    """Testa o banco de dados (SQLite em memória temporária)."""
    print("\n💾 [3/5] Database")

    # Usa um banco temporário para não sujar o real
    import aiosqlite
    original_db = None
    try:
        from db import DB, init_db, close_db, save_user_profile, get_user_profile
        from db import is_job_notified, mark_job_notified, add_subscriber, get_subscribers

        # Redireciona para banco em memória
        import db as db_module
        db_module.DATABASE_PATH = Path(tempfile.gettempdir()) / "jobs_bot_test.db"

        # Limpa banco de teste se existir
        test_path = db_module.DATABASE_PATH
        if test_path.exists():
            test_path.unlink()

        await db_module.init_db()

        # Testa perfil
        await save_user_profile(
            raw_text="Test resume", skills="python, django",
            experience_years=5, desired_roles="Backend",
            locations="Brasil, Remoto"
        )
        profile = await get_user_profile()
        check("Perfil salvo", profile is not None)
        check("Skills corretas", profile["skills"] == "python, django")
        check("Cargo correto", profile["desired_roles"] == "Backend")

        # Testa vagas notificadas
        notified = await is_job_notified("job-123")
        check("Vaga não notificada ainda", not notified)
        await mark_job_notified("job-123", "test", "Dev Python", "Empresa X", "https://ex.com")
        notified = await is_job_notified("job-123")
        check("Vaga marcada como notificada", notified)

        # Testa subscribers
        await add_subscriber("12345")
        await add_subscriber("67890")
        await add_subscriber("12345")  # duplicata — não deve quebrar
        subs = await get_subscribers()
        check(f"Subscribers únicos ({len(subs)})", len(subs) == 2)

        await close_db()
        # Limpa
        if test_path.exists():
            test_path.unlink()

    except Exception as e:
        check(f"DB: {e}", False)
        import traceback
        traceback.print_exc()


async def test_config():
    """Testa o módulo de configuração."""
    print("\n⚙️  [4/5] Config")
    from config import (
        SEARCH_INTERVAL_HOURS, WEEKDAYS_ONLY, MIN_MATCH_SCORE,
        ENABLED_SOURCES, USER_AGENT, REQUEST_TIMEOUT,
    )
    check("SEARCH_INTERVAL_HOURS é inteiro", isinstance(SEARCH_INTERVAL_HOURS, int))
    check("SEARCH_INTERVAL_HOURS > 0", SEARCH_INTERVAL_HOURS > 0)
    check("WEEKDAYS_ONLY é bool", isinstance(WEEKDAYS_ONLY, bool))
    check("MIN_MATCH_SCORE é float", isinstance(MIN_MATCH_SCORE, float))
    check("MIN_MATCH_SCORE entre 0 e 1", 0 < MIN_MATCH_SCORE <= 1)
    check("ENABLED_SOURCES é lista", isinstance(ENABLED_SOURCES, list))
    check("ENABLED_SOURCES tem itens", len(ENABLED_SOURCES) > 0)
    check("ENABLED_SOURCES sem espaços", all(" " not in s for s in ENABLED_SOURCES))


async def test_scheduler_weekday():
    """Testa a trava de dia útil."""
    print("\n📅 [5/5] Scheduler — Dia útil")
    from scheduler import is_weekday
    from datetime import datetime

    today = datetime.now()
    weekday = today.weekday()  # 0=seg .. 6=dom
    day_names = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    is_util = is_weekday()
    print(f"  Hoje é {day_names[weekday]} → {'dia útil' if is_util else 'fim de semana'}")

    if weekday < 5:
        check("Hoje é dia útil — scheduler rodaria", is_util)
    else:
        check("Hoje é fim de semana — scheduler pularia", not is_util)


# ── Main ────────────────────────────────────────────────────────

async def main():
    print("🧪 JobsBot — Teste Offline")
    print("=" * 50)

    await test_resume_parser()
    await test_matcher()
    await test_database()
    await test_config()
    await test_scheduler_weekday()

    print("\n" + "=" * 50)
    total = TESTS_PASSED + TESTS_FAILED
    print(f"📊 Resultado: {TESTS_PASSED}/{total} passaram", end="")
    if TESTS_FAILED:
        print(f", {TESTS_FAILED} falharam ❌")
        sys.exit(1)
    else:
        print(" ✅")
        print("🎉 Todos os testes passaram! O bot está pronto para rodar com rede.")


if __name__ == "__main__":
    asyncio.run(main())