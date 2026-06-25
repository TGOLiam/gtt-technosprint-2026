import uuid

from fastapi import APIRouter, Form, UploadFile

from app.db import get_db
from app.services.audio import convert_to_wav, get_duration_ms, is_silent, save_upload

router = APIRouter(tags=["record"])


@router.post("/api/record")
async def record(
    audio: UploadFile,
    prompt_id: str = Form(""),
    speaker_id: str = Form(""),
    dialect_label: str = Form(...),
    municipality: str = Form(""),
    age_range: str = Form(""),
    gender: str = Form(""),
    license_choice: str = Form("cc0"),
    consent_granted: bool = Form(False),
):

    db = get_db()

    if speaker_id:
        existing = db.execute("SELECT id FROM speakers WHERE id = ?", (speaker_id,)).fetchone()
        if not existing:
            return {"error": "speaker not found", "speaker_id": speaker_id}, 404
    else:
        speaker_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO speakers VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (speaker_id, dialect_label, municipality, age_range, gender, license_choice, int(consent_granted)),
        )

    audio_bytes = await audio.read()
    original_format = audio.content_type or ""

    rec_id, raw_path = save_upload(audio_bytes, original_format)
    wav_path = convert_to_wav(raw_path, rec_id)

    if wav_path is None:
        return {"error": "audio conversion failed"}, 500

    duration_ms = get_duration_ms(wav_path)

    if duration_ms < 500:
        return {"error": "recording too short", "duration_ms": duration_ms}, 400

    if is_silent(wav_path):
        return {"error": "recording is silent"}, 400

    db.execute(
        "INSERT INTO recordings VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
        (rec_id, speaker_id, prompt_id, wav_path, original_format, duration_ms),
    )

    if prompt_id:
        db.execute("UPDATE prompts SET times_recorded = times_recorded + 1 WHERE id = ?", (prompt_id,))

    db.commit()

    naga = db.execute("SELECT COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id WHERE s.dialect_label = 'naga'").fetchone()[0]
    albay = db.execute("SELECT COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id WHERE s.dialect_label = 'albay'").fetchone()[0]

    db.close()

    return {
        "recording_id": rec_id,
        "speaker_id": speaker_id,
        "duration_ms": duration_ms,
        "naga_total": naga,
        "albay_total": albay,
    }
