"""
nlp/scorer.py
"""

import importlib
import logging
import math
import os
import re
import requests
from typing import Optional

from nlp.skills import CATEGORY_WEIGHTS, SKILL_CATEGORY

logger = logging.getLogger(__name__)

# ── Optional heavy imports ────────────────────────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. TF-IDF scoring disabled.")

_SBERT_MODEL: Optional["SentenceTransformer"] = None
_SBERT_AVAILABLE = False

# ── Component weights ─────────────────────────────────────────────────────────
_W_TFIDF = 0.20
_W_SBERT  = 0.55
_W_SKILL  = 0.25

_SBERT_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_sbert() -> Optional["SentenceTransformer"]:
    """Lazy-load the SBERT model only when scoring is requested."""
    global _SBERT_MODEL, _SBERT_AVAILABLE
    if _SBERT_MODEL is not None:
        return _SBERT_MODEL

    try:
        st = importlib.import_module("sentence_transformers")
        SentenceTransformer = getattr(st, "SentenceTransformer")
        _SBERT_MODEL = SentenceTransformer(_SBERT_MODEL_NAME)
        _SBERT_AVAILABLE = True
        logger.info("Loaded SBERT model %s.", _SBERT_MODEL_NAME)
    except Exception as exc:
        _SBERT_AVAILABLE = False
        _SBERT_MODEL = None
        logger.warning("SBERT scoring unavailable: %s", exc)

    return _SBERT_MODEL

# ── ADDED BACK: was missing from your current file ───────────────────────────
def _tfidf_score(resume_text: str, job_text: str) -> float:
    """Cosine similarity between resume and JD using TF-IDF."""
    if not _SKLEARN_AVAILABLE or not resume_text or not job_text:
        return 0.0
    try:
        vectorizer   = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        sim          = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(sim)
    except Exception as exc:
        logger.exception("TF-IDF scoring error: %s", exc)
        return 0.0


def _normalize_skill(skill: str) -> str:
    """'PromptEngineering' → 'prompt engineering', 'LangChain' → 'langchain'"""
    skill = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', skill)
    skill = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', skill)
    return skill.lower().strip()


# ── UPDATED: added sections param and HuggingFace API support ──────────────────
def _sbert_score(resume_text: str, job_text: str, sections: dict = None) -> float:
    if not resume_text or not job_text:
        return 0.0

    hf_token = os.getenv("HUGGINGFACE_API_KEY")
    
    # Don't load local model if we have an API key to save memory
    model = None
    if not hf_token:
        model = _get_sbert()
        if model is None:
            return 0.0

    try:
        sections    = sections or {}
        job_snippet = job_text[:1500]

        priority_sections = ["projects", "experience", "skills", "summary"]
        candidates = []

        for sec in priority_sections:
            if sec in sections and sections[sec].strip():
                candidates.append(sections[sec][:800])

        chunk_size, step = 600, 400
        for i in range(0, len(resume_text), step):
            chunk = resume_text[i:i+chunk_size].strip()
            if chunk:
                candidates.append(chunk)

        if not candidates:
            return 0.0

        all_texts  = candidates + [job_snippet]
        
        if hf_token:
            api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/{_SBERT_MODEL_NAME}"
            headers = {"Authorization": f"Bearer {hf_token}"}
            response = requests.post(api_url, headers=headers, json={"inputs": all_texts, "options": {"wait_for_model": True}})
            response.raise_for_status()
            embeddings = response.json()
            
            if isinstance(embeddings, dict) and "error" in embeddings:
                logger.error(f"HF API Error: {embeddings['error']}")
                return 0.0
        else:
            embeddings = model.encode(all_texts, convert_to_tensor=False)

        job_emb   = embeddings[-1]
        cand_embs = embeddings[:-1]

        sims = []
        for emb in cand_embs:
            dot  = sum(x*y for x,y in zip(emb, job_emb))
            norm = (math.sqrt(sum(x**2 for x in emb)) *
                    math.sqrt(sum(y**2 for y in job_emb))) or 1e-9
            sims.append(float(max(0.0, min(1.0, dot/norm))))

        sims.sort(reverse=True)
        top3    = sims[:3]
        weights = [0.5, 0.3, 0.2]
        return round(sum(s*w for s,w in zip(top3, weights)), 4)

    except Exception as exc:
        logger.exception("SBERT scoring error: %s", exc)
        return 0.0


def _skill_score(resume_text: str, required_skills: list[str]) -> tuple[float, list[str]]:
    if not required_skills:
        return 0.0, []

    text_lower = resume_text.lower()

    def weight(skill: str) -> float:
        cat = SKILL_CATEGORY.get(skill, "tool")
        return CATEGORY_WEIGHTS.get(cat, 1.0)

    total_weight   = 0.0
    matched_weight = 0.0
    matched        = []

    for req_skill in required_skills:
        normalized = _normalize_skill(req_skill)
        w = weight(normalized)
        total_weight += w

        if normalized in text_lower or req_skill.lower() in text_lower:
            matched_weight += w
            matched.append(req_skill)

    score = matched_weight / total_weight if total_weight else 0.0
    return score, matched


# ── UPDATED: added sections param, passed to _sbert_score ────────────────────
def score_candidate(
    resume_text: str,
    job_text: str,
    resume_skills: list[str],
    required_skills: list[str],
    sections: dict = None,          # ← ADDED
) -> dict:
    tfidf_sim            = _tfidf_score(resume_text, job_text)
    sbert_sim            = _sbert_score(resume_text, job_text, sections)  # ← UPDATED
    skill_match, matched = _skill_score(resume_text, required_skills)

    active_components = []
    if _SKLEARN_AVAILABLE:
        active_components.append(("tfidf", tfidf_sim, _W_TFIDF))
    if _SBERT_AVAILABLE or os.getenv("HUGGINGFACE_API_KEY"):
        active_components.append(("sbert", sbert_sim, _W_SBERT))
    active_components.append(("skill", skill_match, _W_SKILL))

    total_weight = sum(w for _, _, w in active_components)
    blended      = sum(v * w for _, v, w in active_components) / (total_weight or 1)
    final_score  = round(blended * 100)

    logger.info(
        "Score → tfidf=%.2f sbert=%.2f skill=%.2f final=%d",
        tfidf_sim, sbert_sim, skill_match, final_score,
    )

    return {
        "score":          final_score,
        "tfidf_sim":      round(tfidf_sim, 4),
        "sbert_sim":      round(sbert_sim, 4),
        "skill_match":    round(skill_match, 4),
        "matched_skills": matched,
    }