
import importlib
import re
import logging
from pathlib import Path

from nlp.skills import ALL_SKILLS, SKILL_ALIASES

logger = logging.getLogger(__name__)

_SPACY_NLP = None


def _get_spacy_nlp():
    """Lazily load spaCy and its small English model if available."""
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP

    try:
        spacy = importlib.import_module("spacy")
        try:
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except OSError:
            # Model may be installed as a separate package
            en_core_web_sm = importlib.import_module("en_core_web_sm")
            _SPACY_NLP = en_core_web_sm.load()
        logger.info("spaCy model loaded successfully.")
    except Exception as exc:
        _SPACY_NLP = None
        logger.warning("spaCy unavailable or model missing: %s", exc)

    return _SPACY_NLP


def _extract_name(text: str) -> str:
    # Strategy 1: spaCy PERSON entity in the first 500 chars
    nlp = _get_spacy_nlp()
    if nlp is not None:
        doc = nlp(text[:500])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()

    # Strategy 2: First non-empty line that looks like a name
    for line in text[:300].splitlines():
        line = line.strip()
        if not line or len(line) > 40 or any(c.isdigit() for c in line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            return line

    return "Unknown"


logger = logging.getLogger(__name__)

# ── Optional pdfplumber import ────────────────────────────────────────────────
try:
    import pdfplumber
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False
    logger.warning("pdfplumber not installed. PDF extraction will be unavailable.")


# ── Regex patterns ─────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
# Very rough name heuristic: 2–4 capitalised words on an early line
_NAME_RE  = re.compile(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})$", re.MULTILINE)


def extract_text(file_path: str) -> str:

    if not _PDF_AVAILABLE:
        logger.error("pdfplumber is not installed; cannot extract text.")
        return ""

    path = Path(file_path)
    if not path.is_file():
        logger.error("PDF not found: %s", file_path)
        return ""

    try:
        with pdfplumber.open(path) as pdf:
            pages_text = [
                page.extract_text() or "" for page in pdf.pages
            ]
        full_text = "\n".join(pages_text).strip()
        logger.info("Extracted %d chars from %s.", len(full_text), path.name)
        return full_text
    except Exception as exc:
        logger.exception("PDF extraction failed for %s: %s", file_path, exc)
        return ""

def _normalize_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        # Convert ALL-CAPS lines under 40 chars to Title Case (likely headers/names)
        if line.isupper() and len(line.strip()) < 40:
            lines.append(line.title())
        else:
            lines.append(line)
    return "\n".join(lines)


def _extract_email(text: str) -> str:
    """Return the first email address found in text, or empty string."""
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    """Return the first phone number found in text, or empty string."""
    match = _PHONE_RE.search(text)
    return match.group(0).strip() if match else ""

def _extract_sections(text: str) -> dict[str, str]:
    """
    Split resume into named sections for targeted scoring.
    Returns dict of section_name → text.
    """
    section_headers = [
        "experience", "projects", "skills", "education",
        "summary", "certifications", "achievements"
    ]
    pattern = re.compile(
        r'(?i)^\s*(' + '|'.join(section_headers) + r')[^\n]*\n',
        re.MULTILINE
    )
    sections = {}
    matches = list(pattern.finditer(text))
    
    for i, match in enumerate(matches):
        name  = match.group(1).lower()
        start = match.end()
        end   = matches[i+1].start() if i+1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    
    return sections

def _resolve(skill: str) -> str:
    return SKILL_ALIASES.get(skill.lower(), skill.lower())
    
def _extract_skills(text: str) -> list[str]:
    """
    Scan the full text for known skills from the master skill list.
    Returns a deduplicated, sorted list of matched skills.
    """
    # text_lower = text.lower()
    # found = sorted({skill for skill in ALL_SKILLS if skill in text_lower})
    # return found
    text_lower = text.lower()
    found = set()
    for skill in ALL_SKILLS:
        if _resolve(skill) in text_lower or skill in text_lower:
            found.add(skill)
    return sorted(found)

def _name_from_filename(stem: str) -> str:
    """'john_doe_resume' → 'John Doe'"""
    words = re.split(r"[_\-\s]+", stem)
    clean = [w.capitalize() for w in words if w.lower() not in ("resume", "cv", "final")]
    return " ".join(clean) if clean else "Unknown"


def parse_resume(file_path: str) -> dict:
   
    raw_text = extract_text(file_path)
    filename_stem = Path(file_path).stem
    if not raw_text:
        return {
            "name": "Unknown",
            "email": "",
            "phone": "",
            "skills": [],
            "raw_text": "",
            "sections": {},
        }
    extracted_name = _extract_name(raw_text)
    return {
        "name":     extracted_name if extracted_name != "Unknown"
                    else _name_from_filename(filename_stem),
        "email":    _extract_email(raw_text),
        "phone":    _extract_phone(raw_text),
        "skills":   _extract_skills(raw_text),
        "raw_text": raw_text,
        "sections": _extract_sections(raw_text),
    }
