from pydantic import BaseModel


class SpeakerCreate(BaseModel):
    id: str
    dialect_label: str
    municipality: str = ""
    age_range: str = ""
    gender: str = ""
    license_choice: str = "cc0"
    consent_granted: bool = False


class PromptOut(BaseModel):
    id: str
    text: str
    dialect_variant: str
    category: str


class RecordingOut(BaseModel):
    id: str
    speaker_id: str
    prompt_id: str
    wav_path: str
    duration_ms: int


class StatsOut(BaseModel):
    total_recordings: int
    naga_count: int
    albay_count: int
    total_speakers: int
    total_duration_minutes: float
    prompts_covered: int
    prompts_total: int
