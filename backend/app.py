"""
app.py
-------
AI-Powered Resume Screening & Candidate Ranking System
Flask backend — all routes live here.

Run:
    python app.py
    
Production:
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

import os
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from firebase.client import db, bucket
from nlp.extractor import parse_resume
from nlp.scorer import score_candidate

# ── Environment & logging ──────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)

CORS(app)

UPLOAD_FOLDER  = os.getenv("UPLOAD_FOLDER", "uploads")
ALLOWED_EXT    = {"pdf"}
MAX_FILE_BYTES = 16 * 1024 * 1024   # 16 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _allowed(filename: str) -> bool:
    """Return True if file has a permitted extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _ok(message: str, data=None, status: int = 200):
    """Consistent success envelope."""
    return jsonify({"success": True, "message": message, "data": data}), status


def _err(message: str, status: int = 400, details=None):
    """Consistent error envelope."""
    payload = {"success": False, "message": message, "data": None}
    if details:
        payload["details"] = details
    return jsonify(payload), status


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """GET /api/health — liveness probe."""
    return _ok("ok", {"service": "resume-screener-api"})

MAX_RAW_TEXT = 15_000

# ── POST /api/upload-resume ────────────────────────────────────────────────────
@app.route("/api/upload-resume", methods=["POST"])
def upload_resume():
    """
    Accept one or more PDF files (field name: 'resumes').
    Saves each file, runs NLP extraction, and stores results in Firestore.
    Returns dummy data if Firestore is unavailable.
    """
    if "resumes" not in request.files:
        return _err("Send PDF files under the field name 'resumes'.", 400)

    files = request.files.getlist("resumes")

    override_name = request.form.get("candidate_name", "").strip()

    if not files or all(f.filename == "" for f in files):
        return _err("No files selected.", 400)

    # Validate extensions
    bad = [f.filename for f in files if not _allowed(f.filename)]
    if bad:
        return _err("Only PDF files are allowed.", 415, {"rejected": bad})
    
    latest_jd = None
    if db:
        from firebase_admin import firestore
        jd_docs = (
            db.collection("job_descriptions")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        jd_doc = next(jd_docs, None)
        if jd_doc:
            latest_jd = jd_doc.to_dict()

    results = []
    for file in files:
        safe_name = secure_filename(file.filename)
        dest      = os.path.join(UPLOAD_FOLDER, safe_name)
        file.save(dest)
        parsed = parse_resume(dest)

        # Auto-score if JD is available
        score_data = {"score": 0, "matched_skills": []}
        if latest_jd and parsed["raw_text"]:
            score_data = score_candidate(
                parsed["raw_text"],
                latest_jd.get("description", ""),
                parsed["skills"],
                latest_jd.get("skills", []),
                sections=parsed["sections"],
            )

        candidate = {
            "filename":      safe_name,
            "name":          override_name if override_name else parsed["name"],
            "email":         parsed["email"],
            "skills":        parsed["skills"],
            "raw_text":      parsed["raw_text"][:MAX_RAW_TEXT],
            "score":         score_data["score"],
            "matched_skills": score_data.get("matched_skills", []),
            "tfidf_sim":     score_data.get("tfidf_sim", 0),
            "sbert_sim":     score_data.get("sbert_sim", 0),
            "skill_match":   score_data.get("skill_match", 0),
            "rank":          None,
            "status":        "reviewed" if latest_jd else "pending",
            "uploaded_at":   datetime.now(timezone.utc).isoformat(),
            "sections": parsed["sections"],
        }

        if db:
            ref = db.collection("candidates").add(candidate)
            candidate["id"] = ref[1].id
        else:
            candidate["id"] = f"local_{safe_name}"

        results.append(candidate)

    return _ok(
        f"{len(results)} resume(s) uploaded and scored.",
        {"candidates": results},
    )


# ── POST /api/job-description ──────────────────────────────────────────────────
@app.route("/api/job-description", methods=["POST"])
def job_description():
    """
    Save a job description and (when candidates exist) trigger re-scoring.

    Expected JSON body:
        {
            "jobTitle":    "Senior Frontend Engineer",
            "description": "We are looking for...",
            "skills":      ["React", "TypeScript"]   ← list OR comma string
        }
    """
    body = request.get_json(silent=True)
    if not body:
        return _err("Request body must be JSON.", 400)

    missing = [f for f in ("jobTitle", "description") if not body.get(f)]
    if missing:
        return _err("Missing required fields.", 400, {"missing": missing})

    # Normalise skills
    raw_skills = body.get("skills", [])
    if isinstance(raw_skills, str):
        skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
    else:
        skills = [s.strip() for s in raw_skills if s.strip()]

    job_doc = {
        "jobTitle":    body["jobTitle"].strip(),
        "description": body["description"].strip(),
        "skills":      skills,
        "created_at":  datetime.now(timezone.utc).isoformat(),
    }

    # Persist to Firestore if available
    job_id = "jd_dummy_001"
    if db:
        ref = db.collection("job_descriptions").add(job_doc)
        job_id = ref[1].id
        logger.info("Job description saved to Firestore: %s", job_id)
    else:
        logger.info("Firestore unavailable — job description not persisted.")

    return _ok("Job description saved.", {**job_doc, "id": job_id}, 201)


# ── GET /api/job-description ──────────────────────────────────────────────────
@app.route("/api/job-description", methods=["GET"])
def get_job_description():
    """Return the most recently created job description."""
    if db:
        try:
            from firebase_admin import firestore
            docs = db.collection("job_descriptions").order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()
            for doc in docs:
                return _ok("Latest job description.", doc.to_dict() | {"id": doc.id})
        except Exception as exc:
            logger.exception("Failed to fetch job description: %s", exc)
    return _ok("No job description found.", None)


# ── POST /api/score ────────────────────────────────────────────────────────────
@app.route("/api/score", methods=["POST"])
def score():
    """
    Accepts job description text and a resume ID.
    Fetches the resume text, computes similarity, updates the score, and returns it.
    """
    body = request.get_json(silent=True)
    if not body:
        return _err("Request body must be JSON.", 400)
    
    resume_id = body.get("resume_id")
    job_text = body.get("job_text")
    job_skills = body.get("job_skills", [])
    
    if not resume_id or not job_text:
        return _err("Missing resume_id or job_text.", 400)
        
    if db:
        doc_ref = db.collection("candidates").document(resume_id)
        doc = doc_ref.get()
        if not doc.exists:
            return _err("Candidate not found.", 404)
        
        cand = doc.to_dict()
        resume_text = cand.get("raw_text", "")
        resume_skills = cand.get("skills", [])
        
        score_data = score_candidate(
            resume_text,
            job_text,
            resume_skills,
            job_skills,
            sections=cand.get("sections", {}),
        )
        
        doc_ref.update({
            "score": score_data["score"],
            "tfidf_sim": score_data.get("tfidf_sim", 0),
            "sbert_sim": score_data.get("sbert_sim", 0),
            "skill_match": score_data.get("skill_match", 0),
            "status": "reviewed",
            "matched_skills": score_data.get("matched_skills", []),
        })
        
        return _ok("Scoring completed.", {"score": score_data["score"], "details": score_data})
    else:
        # Fallback dummy scoring
        return _ok("Scoring completed (dummy).", {"score": 85})


# ── POST /api/score-all ───────────────────────────────────────────────────────
@app.route("/api/score-all", methods=["POST"])
def score_all():
    """
    Score all candidates against a specific job description (by id), or the latest.
    Body (optional JSON): { "jd_id": "<firestore_doc_id>" }
    """
    if not db:
        return _err("Firestore is unavailable.", 500)
        
    from firebase_admin import firestore

    body = request.get_json(silent=True) or {}
    jd_id = body.get("jd_id")

    if jd_id:
        jd_doc = db.collection("job_descriptions").document(jd_id).get()
        if not jd_doc.exists:
            return _err(f"Job description '{jd_id}' not found.", 404)
        job_data = jd_doc.to_dict()
    else:
        # Fall back to latest
        docs = db.collection("job_descriptions").order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()
        jd = next(docs, None)
        if not jd:
            return _err("No job description found.", 404)
        job_data = jd.to_dict()

    job_text = job_data.get("description", "")
    job_skills = job_data.get("skills", [])
    
    # Get all candidates
    candidates_ref = db.collection("candidates").stream()
    updated_count = 0
    for doc in candidates_ref:
        cand = doc.to_dict()
        resume_text = cand.get("raw_text", "")
        resume_skills = cand.get("skills", [])
        
        score_data = score_candidate(
            resume_text,
            job_text,
            resume_skills,
            job_skills,
            sections=cand.get("sections", {}),
        )
        doc.reference.update({
            "score": score_data["score"],
            "tfidf_sim": score_data.get("tfidf_sim", 0),
            "sbert_sim": score_data.get("sbert_sim", 0),
            "skill_match": score_data.get("skill_match", 0),
            "status": "reviewed",
            "matched_skills": score_data.get("matched_skills", [])
        })
        updated_count += 1
        
    return _ok(f"Scored {updated_count} candidates successfully.", {"updated_count": updated_count})


# ── GET /api/candidates ────────────────────────────────────────────────────────
@app.route("/api/candidates", methods=["GET"])
def list_candidates():
    """
    Return all ranked candidates sorted by score descending.

    Query params:
        search  → filter by name / role / skill (case-insensitive)
        sort    → field to sort by (default: score)
        order   → asc | desc  (default: desc)
    """
    # Try Firestore first
    if db:
        try:
            docs = db.collection("candidates").stream()
            candidates = [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as exc:
            logger.exception("Firestore read failed: %s", exc)
            candidates = _dummy_candidates()
    else:
        candidates = _dummy_candidates()

    # Search / filter
    q = request.args.get("search", "").strip().lower()
    if q:
        candidates = [
            c for c in candidates
            if q in c.get("name",  "").lower()
            or q in c.get("role",  "").lower()
            or any(q in s.lower() for s in c.get("skills", []))
        ]

    # Sort
    sort_by = request.args.get("sort",  "score")
    order   = request.args.get("order", "desc").lower()
    reverse = order != "asc"
    if sort_by in ("score", "name", "rank", "experience_years"):
        candidates = sorted(candidates, key=lambda c: c.get(sort_by, 0), reverse=reverse)

    # Re-assign ranks
    for i, c in enumerate(candidates, 1):
        c["rank"] = i

    return _ok(f"{len(candidates)} candidate(s) found.", {"total": len(candidates), "candidates": candidates})


# ── GET /api/candidates/<id> ───────────────────────────────────────────────────
@app.route("/api/candidates/<string:cid>", methods=["GET"])
def get_candidate(cid: str):
    """Return a single candidate by Firestore document ID."""
    if db:
        doc = db.collection("candidates").document(cid).get()
        if not doc.exists:
            return _err(f"Candidate '{cid}' not found.", 404)
        return _ok("Candidate fetched.", doc.to_dict() | {"id": doc.id})

    # Fallback: search dummy data
    match = next((c for c in _dummy_candidates() if c["id"] == cid), None)
    if not match:
        return _err(f"Candidate '{cid}' not found.", 404)
    return _ok("Candidate fetched.", match)


# ── DELETE /api/candidates/<id> ─────────────────────────────────────────────────
@app.route("/api/candidates/<string:cid>", methods=["DELETE"])
def delete_candidate(cid: str):
    """Delete a candidate by Firestore document ID."""
    if db:
        doc_ref = db.collection("candidates").document(cid)
        doc = doc_ref.get()
        if not doc.exists:
            return _err(f"Candidate '{cid}' not found.", 404)
        doc_ref.delete()
        logger.info("Deleted candidate: %s", cid)
        return _ok(f"Candidate '{cid}' deleted successfully.", {"id": cid})
    return _err("Firestore is unavailable.", 503)


# ── GET /api/job-descriptions ──────────────────────────────────────────────────
@app.route("/api/job-descriptions", methods=["GET"])
def list_job_descriptions():
    """Return all job descriptions ordered by creation date (newest first)."""
    if db:
        try:
            from firebase_admin import firestore
            docs = (
                db.collection("job_descriptions")
                .order_by("created_at", direction=firestore.Query.DESCENDING)
                .stream()
            )
            jds = [doc.to_dict() | {"id": doc.id} for doc in docs]
            return _ok(f"{len(jds)} job description(s) found.", {"job_descriptions": jds})
        except Exception as exc:
            logger.exception("Failed to list job descriptions: %s", exc)
            return _err("Failed to fetch job descriptions.", 500)
    return _ok("No job descriptions (Firestore unavailable).", {"job_descriptions": []})


# ── Dummy data (used when Firestore is unavailable) ────────────────────────────

def _dummy_candidates() -> list[dict]:
    return [
        {"id": "cand_001", "name": "Alice Johnson",  "email": "alice@example.com",   "role": "Senior Frontend Engineer", "score": 95, "rank": 1, "match": "Excellent", "skills": ["React", "TypeScript", "Node.js", "GraphQL"], "experience_years": 7, "status": "reviewed"},
        {"id": "cand_002", "name": "Bob Smith",       "email": "bob@example.com",     "role": "Senior Frontend Engineer", "score": 88, "rank": 2, "match": "Strong",    "skills": ["React", "JavaScript", "CSS", "Redux"],      "experience_years": 5, "status": "reviewed"},
        {"id": "cand_003", "name": "Charlie Davis",   "email": "charlie@example.com", "role": "Senior Frontend Engineer", "score": 76, "rank": 3, "match": "Good",      "skills": ["Vue.js", "JavaScript", "TailwindCSS"],      "experience_years": 4, "status": "pending"},
        {"id": "cand_004", "name": "Diana Evans",     "email": "diana@example.com",   "role": "Senior Frontend Engineer", "score": 65, "rank": 4, "match": "Fair",      "skills": ["Angular", "TypeScript", "RxJS"],             "experience_years": 3, "status": "pending"},
        {"id": "cand_005", "name": "Ethan Brown",     "email": "ethan@example.com",   "role": "Senior Frontend Engineer", "score": 58, "rank": 5, "match": "Weak",      "skills": ["HTML", "CSS", "jQuery"],                     "experience_years": 2, "status": "pending"},
    ]


# ── Global error handlers ──────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return _err("Endpoint not found.", 404)

@app.errorhandler(405)
def method_not_allowed(e):
    return _err("Method not allowed.", 405)

@app.errorhandler(413)
def too_large(e):
    return _err("File too large. Maximum is 16 MB.", 413)

@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled error: %s", e)
    return _err("Internal server error.", 500)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "True").lower() == "true",
    )
