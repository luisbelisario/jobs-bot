"""
Motor de embeddings semânticos usando sentence-transformers.
Modelo all-MiniLM-L6-v2: 80MB, gratuito, roda em CPU.
Entende similaridade contextual entre skills, cargos e descrições.
"""
from sentence_transformers import SentenceTransformer
import numpy as np

# Carregamento lazy do modelo (só na primeira chamada)
_MODEL: SentenceTransformer | None = None
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model() -> SentenceTransformer:
    """Retorna o modelo, carregando sob demanda."""
    global _MODEL
    if _MODEL is None:
        print(f"[embeddings] Carregando modelo {_MODEL_NAME}...")
        _MODEL = SentenceTransformer(_MODEL_NAME)
        print("[embeddings] Modelo carregado.")
    return _MODEL


async def profile_embedding(skills: str, roles: str, resume_snippet: str = "") -> np.ndarray:
    """
    Gera o embedding do perfil do usuário.
    Combina skills + roles + trecho do currículo.
    """
    model = _get_model()
    text = f"Skills: {skills}. Roles: {roles}. {resume_snippet[:800]}"
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


async def job_embedding(title: str, description: str) -> np.ndarray:
    """
    Gera o embedding de uma vaga a partir do título e descrição.
    """
    model = _get_model()
    text = f"{title}. {description[:1500]}"
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


async def cosine_similarity(profile_emb: np.ndarray, job_emb: np.ndarray) -> float:
    """Calcula similaridade de cosseno entre dois embeddings."""
    dot = np.dot(profile_emb, job_emb)
    norm = np.linalg.norm(profile_emb) * np.linalg.norm(job_emb)
    if norm == 0:
        return 0.0
    return float(dot / norm)