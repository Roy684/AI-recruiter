"""
firebase/client.py
-------------------
Initialises Firebase Admin SDK (singleton) and exposes
ready-to-use Firestore and Cloud Storage clients.

Usage anywhere in the app:
    from firebase.client import db, bucket
    doc = db.collection("candidates").document(id).get()
"""

import os
import json
import logging

import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Firebase singleton ─────────────────────────────────────────────────────────
_app: firebase_admin.App | None = None


def _init() -> firebase_admin.App | None:
    """Initialise the Firebase Admin SDK once per process."""
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")
    cred_path            = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

    
    try:
        if service_account_json:
            # Running on Render — credentials passed as JSON string in env var
            logger.info("Firebase: loading credentials from FIREBASE_SERVICE_ACCOUNT env var.")
            cred = credentials.Certificate(json.loads(service_account_json))

        elif cred_path and os.path.isfile(cred_path):
            # Running locally — credentials loaded from file
            logger.info("Firebase: loading credentials from file: %s", cred_path)
            cred = credentials.Certificate(cred_path)

        else:
            logger.warning(
                "Firebase: neither FIREBASE_SERVICE_ACCOUNT env var nor "
                "FIREBASE_CREDENTIALS_PATH file found. Running without Firebase."
            )
            return None

        options = {"storageBucket": storage_bucket} if storage_bucket else {}
        app = firebase_admin.initialize_app(cred, options or None)
        logger.info("Firebase initialised (bucket=%s).", storage_bucket or "none")
        return app

    except Exception as exc:
        logger.exception("Firebase init failed: %s", exc)
        return None


def _get_app() -> firebase_admin.App | None:
    global _app
    if _app is not None:
        return _app
    try:
        _app = firebase_admin.get_app()   # already initialised (e.g. in tests)
    except ValueError:
        _app = _init()
    return _app


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_db() -> firestore.Client | None:
    """Return a Firestore client, or None if Firebase is unavailable."""
    if _get_app() is None:
        return None
    try:
        return firestore.client()
    except Exception as exc:
        logger.exception("Firestore client error: %s", exc)
        return None


def get_bucket():
    """Return a Cloud Storage bucket handle, or None if unavailable."""
    if _get_app() is None:
        return None
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()
    if not bucket_name:
        logger.warning(
            "Firebase: FIREBASE_STORAGE_BUCKET not set. "
            "Cloud Storage will be unavailable."
        )
        return None
    try:
        return storage.bucket(bucket_name)
    except Exception as exc:
        logger.exception("Storage bucket error: %s", exc)
        return None


# ── Module-level shortcuts (import these in app.py) ───────────────────────────
db = get_db()
bucket = get_bucket()
