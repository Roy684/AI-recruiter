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
# def _sbert_score(resume_text: str, job_text: str, sections: dict = None) -> float:
#     if not resume_text or not job_text:
#         return 0.0

#     hf_token = os.getenv("HUGGINGFACE_API_KEY")
    
#     # Don't load local model if we have an API key to save memory
#     model = None
#     if not hf_token:
#         model = _get_sbert()
#         if model is None:
#             return 0.0

#     try:
#         sections    = sections or {}
#         job_snippet = job_text[:1500]

#         priority_sections = ["projects", "experience", "skills", "summary"]
#         candidates = []

#         for sec in priority_sections:
#             if sec in sections and sections[sec].strip():
#                 candidates.append(sections[sec][:800])

#         chunk_size, step = 600, 400
#         for i in range(0, len(resume_text), step):
#             chunk = resume_text[i:i+chunk_size].strip()
#             if chunk:
#                 candidates.append(chunk)

#         if not candidates:
#             return 0.0

#         if hf_token:
#             from huggingface_hub import InferenceClient
#             client = InferenceClient(api_key=hf_token)
#             # This may return a list of floats or a list of dicts depending on client version.
#             sims = client.sentence_similarity(
#                 source_sentence=job_snippet,
#                 sentences=candidates,
#                 model=f"sentence-transformers/{_SBERT_MODEL_NAME}"
#             )
#             if isinstance(sims, dict):
#                 sims = sims.get("scores") or sims.get("result") or []
#             if sims and isinstance(sims[0], dict):
#                 sims = [float(item.get("score", item.get("similarity", item.get("value", 0.0)))) for item in sims]
#         else:
#             all_texts  = candidates + [job_snippet]
#             embeddings = model.encode(all_texts, convert_to_tensor=False)

#             job_emb   = embeddings[-1]
#             cand_embs = embeddings[:-1]

#             sims = []
#             for emb in cand_embs:
#                 dot  = sum(x*y for x,y in zip(emb, job_emb))
#                 norm = (math.sqrt(sum(x**2 for x in emb)) *
#                         math.sqrt(sum(y**2 for y in job_emb))) or 1e-9
#                 sims.append(float(max(0.0, min(1.0, dot/norm))))

#         sims.sort(reverse=True)
#         top3    = sims[:3]
#         weights = [0.5, 0.3, 0.2]
#         return round(sum(s*w for s,w in zip(top3, weights)), 4)

#     except Exception as exc:
#         logger.exception("SBERT scoring error: %s", exc)
#         return 0.0


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

def _sbert_score(resume_text: str, job_text: str, sections: dict = None) -> float:
    if not resume_text or not job_text:
        print("SBERT: missing resume_text or job_text")
        return 0.0

    hf_token = os.getenv("HUGGINGFACE_API_KEY", "").strip()
    print("SBERT: hf_token present:", bool(hf_token))

    sections    = sections or {}
    job_snippet = job_text[:1500]

    # Build candidate chunks
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

    print(f"SBERT: built {len(candidates)} resume chunks from sections + raw_text")
    if not candidates:
        logger.warning("SBERT: no candidate chunks built from resume text.")
        print("SBERT: returning 0.0 because no candidates were built")
        return 0.0

    try:
        if hf_token:
            print("SBERT: using HuggingFace API path")
            sims = _hf_api_similarity(job_snippet, candidates, hf_token)
        else:
            print("SBERT: using local model path")
            sims = _local_sbert_similarity(job_snippet, candidates)

        print("SBERT: raw sims result:", sims)
        if not sims:
            logger.warning("SBERT: similarity list is empty after scoring.")
            print("SBERT: returning 0.0 because sims list is empty")
            return 0.0

        sims.sort(reverse=True)
        top3    = sims[:3]
        weights = [0.5, 0.3, 0.2][:len(top3)]
        # Re-normalize weights if fewer than 3 chunks
        total_w = sum(weights)
        result  = round(sum(s*w for s,w in zip(top3, weights)) / total_w, 4)
        print(f"SBERT: top3={top3} result={result}")
        logger.info("SBERT: top3=%s final=%.4f", top3, result)
        return result

    except Exception as exc:
        logger.exception("SBERT scoring error: %s", exc)
        print("SBERT: exception during scoring:", exc)
        return 0.0


def _hf_api_similarity(job_snippet: str, candidates: list, hf_token: str) -> list:
    """Call HuggingFace Inference API for sentence similarity."""
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=hf_token)
        print("SBERT: calling HF client.sentence_similarity with", len(candidates), "candidates")
        sims = client.sentence_similarity(
            sentence=job_snippet,
            other_sentences=candidates,
            model=f"sentence-transformers/{_SBERT_MODEL_NAME}"
        )
        print("SBERT: HF raw sims:", sims)
        if isinstance(sims, list):
            return [float(x) for x in sims]
        logger.error("HF client returned unexpected similarity format: %s", type(sims))
        print("SBERT: HF unexpected sims type", type(sims), sims)
        return []
    except ImportError as exc:
        logger.error("huggingface_hub is unavailable: %s", exc)
        print("SBERT: huggingface_hub import failed:", exc)
        return []
    except Exception as exc:
        logger.exception("HF sentence_similarity error: %s", exc)
        print("SBERT: HF sentence_similarity exception:", exc)
        return []


def _local_sbert_similarity(job_snippet: str, candidates: list) -> list:
    """Use local sentence-transformers model."""
    print("SBERT: using local model path")
    model = _get_sbert()
    if model is None:
        print("SBERT: local model unavailable")
        return []

    print("SBERT: local model loaded, encoding", len(candidates) + 1, "texts")
    all_texts  = candidates + [job_snippet]
    embeddings = model.encode(all_texts, convert_to_tensor=False)

    job_emb   = embeddings[-1]
    cand_embs = embeddings[:-1]

    sims = []
    for emb in cand_embs:
        dot  = sum(x*y for x,y in zip(emb, job_emb))
        norm = (math.sqrt(sum(x**2 for x in emb)) *
                math.sqrt(sum(y**2 for y in job_emb))) or 1e-9
        sims.append(float(max(0.0, min(1.0, dot/norm))))
    print("SBERT: local sims", sims)
    return sims


def score_candidate(
    resume_text: str,
    job_text: str,
    resume_skills: list[str],
    required_skills: list[str],
    sections: dict = None,
) -> dict:
    tfidf_sim            = _tfidf_score(resume_text, job_text)
    sbert_sim            = _sbert_score(resume_text, job_text, sections)
    skill_match, matched = _skill_score(resume_text, required_skills)

    active_components = []
    if _SKLEARN_AVAILABLE:
        active_components.append(("tfidf", tfidf_sim, _W_TFIDF))

    # ── FIXED: sbert is active if we got a non-zero score ────────────────────
    # Don't gate on _SBERT_AVAILABLE flag — if the score came back, use it
    if sbert_sim > 0.0:
        active_components.append(("sbert", sbert_sim, _W_SBERT))
    else:
        logger.warning("SBERT score is 0 — excluded from blended score. "
                       "Check HUGGINGFACE_API_KEY env var on Render.")

    active_components.append(("skill", skill_match, _W_SKILL))

    total_weight = sum(w for _, _, w in active_components)
    blended      = sum(v * w for _, v, w in active_components) / (total_weight or 1)
    final_score  = round(blended * 100)

    logger.info(
        "Score → tfidf=%.2f sbert=%.2f skill=%.2f final=%d (components=%s)",
        tfidf_sim, sbert_sim, skill_match, final_score,
        [c[0] for c in active_components]
    )

    return {
        "score":          final_score,
        "tfidf_sim":      round(tfidf_sim, 4),
        "sbert_sim":      round(sbert_sim, 4),
        "skill_match":    round(skill_match, 4),
        "matched_skills": matched,
    }
# ── UPDATED: added sections param, passed to _sbert_score ────────────────────
# def score_candidate(
#     resume_text: str,
#     job_text: str,
#     resume_skills: list[str],
#     required_skills: list[str],
#     sections: dict = None,          # ← ADDED
# ) -> dict:
#     tfidf_sim            = _tfidf_score(resume_text, job_text)
#     sbert_sim            = _sbert_score(resume_text, job_text, sections)  # ← UPDATED
#     skill_match, matched = _skill_score(resume_text, required_skills)

#     active_components = []
#     if _SKLEARN_AVAILABLE:
#         active_components.append(("tfidf", tfidf_sim, _W_TFIDF))
#     if _SBERT_AVAILABLE or os.getenv("HUGGINGFACE_API_KEY"):
#         active_components.append(("sbert", sbert_sim, _W_SBERT))
#     active_components.append(("skill", skill_match, _W_SKILL))

#     total_weight = sum(w for _, _, w in active_components)
#     blended      = sum(v * w for _, v, w in active_components) / (total_weight or 1)
#     final_score  = round(blended * 100)

#     logger.info(
#         "Score → tfidf=%.2f sbert=%.2f skill=%.2f final=%d",
#         tfidf_sim, sbert_sim, skill_match, final_score,
#     )

#     return {
#         "score":          final_score,
#         "tfidf_sim":      round(tfidf_sim, 4),
#         "sbert_sim":      round(sbert_sim, 4),
#         "skill_match":    round(skill_match, 4),
#         "matched_skills": matched,
#     }