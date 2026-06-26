import uuid
import yaml
from enum import Enum
from contextlib import closing
from pathlib import Path

from fastapi import APIRouter, Form, UploadFile, Request
from fastapi.responses import JSONResponse

from app.db import get_db
from app.services.audio import save_upload

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["record"])

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "input" / "manifest.yml"

class Dialect(str, Enum):
    naga = "naga"
    albay = "albay"


def update_manifest(audio_path: str, dialect_label: str, rec_id: str):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r") as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {
            "defaults": {
                "confidence": "high",
                "segment": {
                    "max_duration_s": 10,
                    "min_duration_s": 1
                }
            },
            "files": []
        }

    if "files" not in manifest or manifest["files"] is None:
        manifest["files"] = []

    manifest["files"].append({
        "path": Path(audio_path).name,  # just the filename, not full path
        "dialect_label": dialect_label,
        "source_name": rec_id,
        "source_type": "app_recording"
    })

    with open(MANIFEST_PATH, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)


@router.post("/api/record")
@limiter.limit("10/minute")
async def record(
    request: Request,
    audio: UploadFile,
    prompt_id: str = Form(""),
    speaker_id: str = Form(""),
    dialect_label: Dialect = Form(...),
    municipality: str = Form(""),
    age_range: str = Form(""),
    gender: str = Form(""),
    license_choice: str = Form("cc0"),
    consent_granted: bool = Form(False),
):
    audio_bytes = await audio.read()
    original_format = audio.content_type or ""
    rec_id, audio_path = save_upload(audio_bytes, original_format)

    update_manifest(audio_path, dialect_label.value, rec_id)

    with closing(get_db()) as db:
        if speaker_id:
            existing = db.execute("SELECT id FROM speakers WHERE id = ?", (speaker_id,)).fetchone()
            if not existing:
                db.execute(
                    "INSERT INTO speakers VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                    (speaker_id, dialect_label, municipality, age_range, gender, license_choice, int(consent_granted)),
                )
        else:
            speaker_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO speakers VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (speaker_id, dialect_label, municipality, age_range, gender, license_choice, int(consent_granted)),
            )

        db.execute(
            "INSERT INTO recordings VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            (rec_id, speaker_id, prompt_id or None, audio_path, original_format, 0),
        )

        if prompt_id:
            db.execute("UPDATE prompts SET times_recorded = times_recorded + 1 WHERE id = ?", (prompt_id,))

        db.commit()

        naga = db.execute("SELECT COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id WHERE s.dialect_label = 'naga'").fetchone()[0]
        albay = db.execute("SELECT COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id WHERE s.dialect_label = 'albay'").fetchone()[0]

    return {
        "recording_id": rec_id,
        "speaker_id": speaker_id,
        "naga_total": naga,
        "albay_total": albay,
    }