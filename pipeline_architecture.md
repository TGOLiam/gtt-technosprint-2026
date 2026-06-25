# Bikol Speech Preprocessing Pipeline — Architecture

## Overview

```
                      INPUT SOURCES
         ┌────────────────┼────────────────┐
         │                │                │
  scrape_audio.py    app recordings    manual uploads
  (sources.yaml)     (backend/data/)   (drag-and-drop)
         │                │                │
         └────────────────┼────────────────┘
                          │
              raw/{source}/ + sidecar JSON
                          │
         ╔════════════════╧════════════════╗
         ║        postprocess.py           ║
         ║                                ║
         ║  Stage 1: NORMALIZE (ffmpeg)   ║
         ║  Stage 2: SEGMENT  (ffmpeg)    ║
         ║  Stage 3: CLASSIFY (MMS-LID)   ║
         ║                                ║
         ╚════════════════╤════════════════╝
                          │
              pipeline/output/
              ├── audio/*.wav
              ├── rejected/*.wav
              ├── manifest.csv
              ├── rejected.csv
              └── pipeline.log
```

<<<<<<< HEAD
**postprocess.py** walks `raw/` looking for `*.json` sidecars. For each one, if a matching audio/video file exists with the same basename, it runs the three-stage pipeline. If no sidecar, the file is skipped.
=======
The pipeline reads a single `manifest.yml` from the input directory that labels
every media file and configures per-file processing parameters. Each file goes
through three stages. The output receives segmented WAVs with dual-signal
metadata: the user's claimed `dialect_label` alongside MMS-LID's `predicted_lang`.

---

## CLI

```
python pipeline/run.py <input_dir> <output_dir>

Options:
  --skip-classify   Run only stages 1-2, skip language classification
  --keep-temp       Keep temporary files for debugging
  -v, --verbose     Print per-file progress
```

`output_dir` is cleared before each run. Both arguments are required.

Temp files go to system temp (`/tmp/pipeline_{uuid}/`) and are cleaned after
the run unless `--keep-temp` is passed.

### Run Summary (GPU)

```
$ python pipeline/run.py my_batch/ output/

Stage 1 (normalize):  5/5 files ✓
Stage 2 (segment):    42 segments
Stage 3 (classify):   Using CUDA (NVIDIA GeForce RTX 3060)
                      42/42 classified in 4.2s (31 kept, 11 rejected)

Output:
  output/audio/                     31 segments
  output/rejected/                  11 segments
  output/manifest.csv               31 rows
  output/rejected.csv               11 rows
  output/pipeline.log               58 lines

Done.
```

### Run Summary (CPU)

```
$ python pipeline/run.py my_batch/ output/

Stage 1 (normalize):  5/5 files ✓
Stage 2 (segment):    42 segments
Stage 3 (classify):   Downloading MMS-LID-256 (3.9 GB, one-time)...
                      ⚠ No GPU detected — running on CPU (5-15s/clip)
                      For faster processing, see the Colab fallback below.
                      42/42 classified in 4m 12s (31 kept, 11 rejected)

Output:
  output/audio/                     31 segments
  output/rejected/                  11 segments
  output/manifest.csv               31 rows
  output/rejected.csv               11 rows
  output/pipeline.log               58 lines

Done.
```

### Colab Fallback

If your machine lacks a GPU, the Colab notebook processes Stage 3 on a free
T4 GPU (~100× faster than CPU):

1. Run stages 1-2 locally: `python pipeline/run.py my_batch/ output/ --skip-classify`
2. The segmented WAVs are in `output/audio/`
3. Open `pipeline/validate.ipynb` in [Google Colab](https://colab.research.google.com/)
4. Upload `output/audio/` as a zip → Runtime → Run All
5. Download `manifest.csv` and `rejected.csv`, place in `output/`
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)

---

## Input Contract

### Sidecar JSON Format

<<<<<<< HEAD
Each audio source must have a sidecar `*.json` next to it:

```json
{
  "dialect_label": "naga",
  "confidence": "high",
  "source_name": "bible-central-bikol",
  "source_type": "bible_api"
}
=======
```yaml
# Global defaults — applied to all files unless overridden
defaults:
  dialect_label: naga
  confidence: high
  segment:
    max_duration_s: 10
    min_duration_s: 1

# Per-file entries
files:
  - path: MAT_01.mp3
    source_name: bible-central-bikol

  - path: MAT_02.mp3
    source_name: bible-central-bikol

  - path: interview.mp4
    dialect_label: albay
    confidence: inferred
    source_type: field_recording
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)
```

All four fields are required.

| Field | Values | Description |
|---|---|---|
| `dialect_label` | `naga`, `albay`, or any string | Passed through to output. The pipeline does NOT validate or constrain this field. |
| `confidence` | `high`, `medium`, `inferred` | How trustworthy is the label. Propagated to manifest.csv. |
| `source_name` | string matching a `sources.yaml` entry | For provenance. |
| `source_type` | `bible_api`, `huggingface`, `ytdlp`, `radio_stream`, `app_recording`, `manual` | How the audio was acquired. |

### Supported Audio Formats

Any format ffmpeg can read: `.mp3`, `.mp4`, `.wav`, `.webm`, `.ogg`, `.m4a`, `.flac`, `.mov`, `.mkv`, `.aac`, `.opus`, `.wma`, `.3gp`.

Video files are accepted — ffmpeg extracts the first audio stream.

### File Naming Convention

The sidecar and audio file must share the same basename:

```
raw/bible-central-bikol/MAT_01.mp3
raw/bible-central-bikol/MAT_01.json       ← sidecar
```

If `MAT_01.json` exists but `MAT_01.mp3` doesn't, skip. If multiple audio files share a basename (e.g., `MAT_01.mp3` and `MAT_01.wav`), both are processed with the same sidecar labels.

---

## Stage 1: NORMALIZE

### Input → Output

```
raw/{source}/{name}.{ext}   (any format)
     │
     ▼
ffmpeg -y -i input -ar 16000 -ac 1 -sample_fmt s16 output.wav
     │
     ▼
temp/normalized/{source}/{name}.wav
```

### Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Resample rate | 16kHz | Standard for speech ML |
| 2 | Channel count | Mono (downmix) | Pipeline doesn't need stereo |
| 3 | Bit depth | Signed 16-bit PCM | Widest compatibility, smallest size |
| 4 | Volume normalization | None | Not the pipeline's job. Users can normalize downstream. |
| 5 | Audio stream selection | First stream | Default ffmpeg behavior. No override in v1. |
| 6 | Corrupted file | Log, skip, continue | Don't abort the whole pipeline for one bad file |
| 7 | Wrong extension (mp3 named .wav) | ffmpeg probes container | Works in most cases. No extension validation in v1. |
| 8 | Missing audio stream (image file) | ffmpeg fails | Logged as error, skipped |
| 9 | Temp file location | `temp/normalized/{source}/` | Deleted after Stage 3 completes |
| 10 | ffmpeg subprocess timeout | 5 minutes per file | Prevents hanging on corrupt/endless streams |

### Errors

| Error | Cause | Pipeline Behavior |
|---|---|---|
| `ffmpeg_fail` | Corrupt file, unsupported format, no audio stream | Log, skip all segments for this file |
| `ffmpeg_timeout` | File too large, stuck decode | Log, skip |

### Log Entry (one per input file)

```json
{"ts": "2026-06-25T15:00:00", "stage": "normalize", "file": "bible-central-bikol/MAT_01.mp3", "status": "ok", "output": "temp/normalized/bible-central-bikol/MAT_01.wav", "duration_ms": 120000}
```

For failures:

```json
{"ts": "2026-06-25T15:00:00", "stage": "normalize", "file": "bible-central-bikol/bad.mp3", "status": "fail", "error": "ffmpeg: unrecognized format"}
```

---

## Stage 2: SEGMENT

### Input → Output

```
temp/normalized/{source}/{name}.wav   (16kHz mono, any duration)
     │
     ▼
If duration ≤ max_duration_s  → one segment, as-is
If duration > max_duration_s  → split into N chunks of exactly max_duration_s
                                  last chunk: keep if ≥ min_duration_s, discard otherwise
     │
     ▼
temp/segmented/{source}/{name}_000.wav
temp/segmented/{source}/{name}_001.wav
temp/segmented/{source}/{name}_002.wav
...
```

### Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Segmentation method | Hard cut (ffmpeg `-segment_time`) | Simple, predictable, no model dependency |
| 2 | Max segment duration | 10s (configurable) | Long enough for LID to work, short enough for downstream use |
| 3 | Min segment duration | 1s (configurable) | Shorter = noise, clicks, not useful speech |
| 4 | VAD-based segmentation | Skipped | Stage 3 (LID) catches silence/noise. Two-stage gatekeeping is simpler. |
| 5 | Cuts mid-word | Allowed | Dialect classification doesn't need semantic coherence. LID works on sub-second audio. |
| 6 | Overlap between segments | None | Clean cuts |

### Configuration

Defaults (applied if source has no `segment` block):

```yaml
segment:
  max_duration_s: 10
  min_duration_s: 1
```

Per-source override:

```yaml
# Radio stream with longer talk segments
segment:
  max_duration_s: 15

# Short utterance dataset
segment:
  max_duration_s: 5
```

### What Happens Per File

| Duration | Result |
|---|---|
| 0.5s | Discarded (< min) |
| 1s | One segment |
| 8s | One segment |
| 10s | One segment |
| 10.5s | One segment (≤ max, no split) |
| 45s | Five segments: 4 × 10s + 1 × 5s |
| 41s | Five segments: 4 × 10s + 1 × 1s (exactly at min) |
| 39.5s | Four segments: 3 × 10s + 1 × 9.5s |
| 30s | Three 10s segments |

The "one segment if ≤ max" rule means a 10s file produces one segment, not two 5s chunks. The split only triggers when duration exceeds `max_duration_s`.

### Errors

| Error | Cause | Behavior |
|---|---|---|
| `segment_too_short` | Entire file < min_duration_s | Log, skip all segments |
| `no_segments` | All chunks < min_duration_s | Log, skip |

### Log Entry (one per input file)

```json
{"ts": "2026-06-25T15:00:01", "stage": "segment", "file": "temp/normalized/bible-central-bikol/MAT_01.wav", "status": "ok", "input_duration_ms": 120000, "segments": 12, "avg_duration_ms": 10000}
```

---

## Stage 3: CLASSIFY

### Input → Output

```
temp/segmented/{source}/{name}_000.wav   (≤ max_duration_s)
     │
     ▼
Model: facebook/mms-lid-256
     │  Inference returns [(lang, score), ...]
     │
<<<<<<< HEAD
     ├── top-1 lang ∈ accepted_langs AND score ≥ min_score → KEEP → output/audio/
     └── otherwise → REJECT → output/rejected/
=======
      ├── lang ∈ known PH codes → KEEP → output_dir/audio/
      └── otherwise → REJECT → output_dir/rejected/
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)
```

### Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | LID model | `facebook/mms-lid-256` | Only model covering Bikol (`bcl`). Transformers pipeline. |
| 2 | Inference method | HuggingFace `pipeline("audio-classification")` | Simplest integration. torch dependency. |
<<<<<<< HEAD
| 3 | Default accepted langs | `[bcl, bik, ubl, ...]` + `[tgl, ceb, war, ilo, hil, ...]` | Bikol codes PLUS other Philippine languages. MMS-LID often misclassifies conversational Bikol as Tagalog or Cebuano due to training data composition (religious text only). Wider gate reduces false negatives. Metadata records the actual LID prediction so downstream users can filter post-hoc. |
| 4 | Default min score | 0.3 | Low bar. False negatives worse than false positives for speech data. |
| 5 | Batching | One segment at a time | Simplest. Batch processing adds complexity without urgency for v1. |
| 6 | Model loading | Load once at pipeline start | Avoid reloading 4GB model per segment. |
| 7 | Rejected audio | Saved to `output/rejected/` | Proves pipeline is honest. Users can inspect false negatives. |
| 8 | Score precision | Four decimal places | Enough for downstream filtering. |
=======
| 3 | Gate logic | PH language filter: `{bcl, bto, ubl, tgl, ceb, ilo, hil, war}` | MMS-LID often misclassifies conversational Bikol as Tagalog or Cebuano. Wider gate reduces false negatives. `manifest.csv` records both `dialect_label` (user claim) and `predicted_lang` (MMS prediction) for downstream filtering. |
| 4 | Batching | One segment at a time | Simplest. Batch processing adds complexity without urgency for v1. |
| 5 | Model loading | Load once at pipeline start | Avoid reloading 4GB model per segment. |
| 6 | Rejected audio | Saved to `output_dir/rejected/` | Proves pipeline is honest. Users can inspect false negatives. |
| 7 | Score precision | Four decimal places | Enough for downstream filtering. |
| 8 | GPU usage | Auto-detect via `torch.cuda.is_available()`. No config required. | `transformers` pipeline loads to GPU automatically. MPS (Apple Silicon) also supported. Falls back to CPU silently with a warning pointing to the Colab fallback. |
| 9 | Model cache | `pipeline/models/` via `cache_dir` | Keeps 3.9 GB model in project tree. One-time download. gitignored. `HF_HOME` env var overrides. |

### GPU Detection

`validate.py` checks for hardware acceleration at startup:

```
GPU check on startup:
  ├── CUDA available?    → model loads on GPU     → ~0.1s per clip
  ├── MPS available?     → model loads on MPS     → ~0.3-0.5s per clip
  └── neither            → stays on CPU           → 5-15s per clip
                                    │
                                    ▼
                        ⚠ "No GPU detected. Stage 3 will run on CPU
                           (5-15s per clip). For large batches,
                           see the Colab fallback below."
```

The CPU warning prints once and includes a direct link to the Colab notebook.
If GPU is available, no message is printed — it just works silently.

### Model Storage

The model is downloaded once on first run and cached for subsequent runs.

```python
model = pipeline(
    "audio-classification",
    model="facebook/mms-lid-256",
    cache_dir="pipeline/models/",
)
```

| Behavior | Details |
|---|---|
| Default location | `~/.cache/huggingface/` |
| Project convention | `pipeline/models/models--facebook--mms-lid-256/` via `cache_dir` |
| Disk size | ~3.9 GB (safetensors format) |
| First run | Downloads model from HuggingFace (~30-60s) |
| Subsequent runs | Loads from cache (instant) |
| gitignored | `pipeline/models/` is in `.gitignore` |

Users can override the cache location via the `HF_HOME` environment variable
if they prefer a different path.
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)

### Accepted Language Codes

The pipeline uses a **Philippine language filter** rather than a strict Bikol-only check. This is because MMS-LID-256 was trained on FLEURS (religious text readings) and often misclassifies conversational Bikol as Tagalog, Cebuano, or other Philippine languages with more training data.

All Bikol macrolanguage codes plus related Philippine language codes are accepted. The `manifest.csv` records what MMS-LID *actually* predicted (`bikol_lang` column) so downstream users can apply stricter filtering if needed.

**Bikol codes (primary target):**

| Code | Variety |
|---|---|
| `bcl` | Central Bikol (Naga/Coastal) |
| `ubl` | Buhi'non (Albay) |
| `lbl` | Libon Bikol |
| `rbl` | Miraya Bikol |
| `fbl` | West Albay Bikol |
| `bto` | Rinconada Bikol |
| `bln` | Southern Catanduanes Bikol |
| `cts` | Northern Catanduanes Bikol |
| `bik` | Bikol (macrolanguage) |

<<<<<<< HEAD
All codes are ISO 639-3 standard, assigned by SIL International. Model coverage verified only for `bcl` and `bik` — the other codes may or may not be recognized by MMS-LID-256. If unrecognized, those segments will be rejected as `not_bikol`. Users can tighten the accepted list per source.
=======
**Related Philippine codes (accepted to reduce false negatives):**

| Code | Language |
|---|---|
| `tgl` | Tagalog |
| `ceb` | Cebuano |
| `war` | Waray |
| `ilo` | Ilocano |
| `hil` | Hiligaynon |
| `pam` | Kapampangan |
| `pag` | Pangasinan |
| `mdh` | Maguindanao |
| `mrw` | Maranao |

All codes are ISO 639-3 standard, assigned by SIL International. Model
coverage verified only for `bcl` and `bik` — the other codes may or may not
be recognized by MMS-LID-256. If unrecognized, those segments are rejected as
<<<<<<< HEAD
`not_bikol`.
>>>>>>> 75e77e0 (widen accepted_langs to include Philippine languages, document rationale)

### Configuration

```yaml
validate:
  accepted_langs: [bcl, bik]    # override — only Central Bikol for this source
  min_score: 0.3
```
=======
`not_ph_language`.
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)

If `validate` block is absent, defaults apply.

### Log Entry (one per segment)

Keep:

```json
<<<<<<< HEAD
{"ts": "2026-06-25T15:00:02", "stage": "validate", "segment": "temp/segmented/bible-central-bikol/MAT_01_000.wav", "status": "keep", "top_lang": "bcl", "score": 0.9421}
=======
{"ts": "2026-06-25T15:00:02", "stage": "classify", "segment": "MAT_01_000.wav", "status": "keep", "lang": "bcl", "score": 0.9421}
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)
```

Reject:

```json
<<<<<<< HEAD
{"ts": "2026-06-25T15:00:03", "stage": "validate", "segment": "temp/segmented/bible-central-bikol/MAT_01_005.wav", "status": "reject", "top_lang": "eng", "score": 0.8732, "reason": "not_bikol"}
```

```json
{"ts": "2026-06-25T15:00:04", "stage": "validate", "segment": "temp/segmented/bible-central-bikol/MAT_01_012.wav", "status": "reject", "top_lang": "bcl", "score": 0.2103, "reason": "low_confidence"}
=======
{"ts": "2026-06-25T15:00:03", "stage": "classify", "segment": "MAT_01_005.wav", "status": "reject", "lang": "eng", "score": 0.8732, "reason": "not_ph_language"}
```
>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)
```

---

## Output Schema

### manifest.csv

| Column | Type | Source |
|---|---|---|
| `segment_id` | `{dialect_label}_{counter:05d}` | Generated, resets per dialect per run |
| `wav_path` | `audio/{segment_id}.wav` | Relative path |
| `dialect_label` | string | From sidecar JSON |
| `confidence` | `high` \| `medium` \| `inferred` | From sidecar JSON |
| `source_name` | string | From sidecar JSON |
| `source_type` | string | From sidecar JSON |
| `duration_ms` | integer | ffprobe on segment WAV |
| `predicted_lang` | ISO code (e.g. `bcl`) | MMS-LID top-1 language |
| `predicted_score` | 0.0–1.0 | MMS-LID confidence |

### rejected.csv

Same columns, plus:

| Column | Type |
|---|---|
| `reject_reason` | `not_ph_language`, `lid_error` |

### pipeline.log

JSONL format. One line per event. Events include:

- `normalize` — one per input file (success or failure)
- `segment` — one per input file (count of segments produced)
- `classify` — one per segment (keep or reject)

---

## Configuration (`sources.yaml`)

### Full Schema

```yaml
naga:                               # top-level key = dialect label
  - name: bible-central-bikol       # unique source identifier
    type: bible_api                 # source type (informational)
    iso: bcl                        # source-specific fields
    confidence: high                # high | medium | inferred
    audio: true                     # this source provides audio
    text: true                      # this source provides text (for prompts)
    segment:                        # optional — overrides Stage 2 defaults
      max_duration_s: 10
      min_duration_s: 1
    validate:                       # optional — overrides Stage 3 defaults
      accepted_langs: [bcl, bik]
      min_score: 0.3
```

The sidecar JSON is the authority, not `sources.yaml`. If the sidecar says `dialect_label: albay` but the source is listed under `naga:` in sources.yaml, the sidecar wins. sources.yaml provides defaults; the sidecar provides per-file overrides.

---

## File Layout

```
scraper/
├── sources.yaml              # source registry + pipeline config
├── scrape_audio.py           # downloads raw audio + sidecars
├── extract_prompts.py        # generates prompts.csv (separate concern)
├── postprocess.py            # THE PIPELINE
├── requirements.txt          # dependencies
│
├── raw/                      # downloads (gitignored)
│   ├── bible-central-bikol/
│   │   ├── MAT_01.mp3
│   │   ├── MAT_01.json       ← sidecar
│   │   ├── MAT_02.mp3
│   │   └── MAT_02.json
│   └── bible-buhinon/
│       ├── MAT_01.mp3
│       └── MAT_01.json
│
├── temp/                     # transient (gitignored, deleted after run)
│   ├── normalized/
│   └── segmented/
│
└── output/                   # pipeline output (gitignored except README)
    ├── README.md
    ├── audio/
    │   ├── naga_00001.wav
    │   ├── naga_00002.wav
    │   ├── albay_00001.wav
    │   └── ...
    ├── rejected/
    │   ├── naga_00015.wav
    │   └── ...
    ├── manifest.csv
    ├── rejected.csv
    └── pipeline.log
```

### App Recording Bridge

The pipeline can also ingest app recordings from `backend/data/audio/`. A bridge script (`backend_to_pipeline.py`) generates sidecar JSONs from the backend SQLite database:

```python
# For each recording in recordings:
#   1. Read speaker.dialect_label from speakers table
#   2. Write sidecar JSON next to the WAV file
#   3. Pipeline processes like any other source
```

---

## Runtime

### CLI

```bash
python scraper/postprocess.py
```

No arguments. Reads `sources.yaml` for defaults. Walks `raw/` for sidecars.

### Run Summary (stdout)

```
╔══════════════════════════════════════════════╗
║       Bikol Speech Preprocessing Pipeline     ║
╚══════════════════════════════════════════════╝

Sources found: 6 (naga=4, albay=2)
  albay-youtube            disabled (no audio)
  bikol-wikipedia          text-only, skipping

Input files: 48
  Stage 1 (normalize):   48 ok, 0 failed
  Stage 2 (segment):    312 segments from 48 files (avg 6.5 per file)
  Stage 3 (validate):   247 kept, 65 rejected (79.2%)

Reject reasons:
  not_bikol:         41 (63.1%)
  low_confidence:    18 (27.7%)
  too_short:          6 (9.2%)

Output:
  audio/naga_*.wav:        175 segments
  audio/albay_*.wav:        72 segments
  manifest.csv:            247 rows
  rejected.csv:             65 rows
  pipeline.log:            425 lines

Done in 12m 34s.
```

### Caching

Segment IDs are deterministic per input file. If a segment already exists in `output/audio/` with the same ID, Stage 3 is skipped for that segment. Re-runs only validate new files.

If `sources.yaml` or the LID model changes, delete `output/` and re-run from scratch.

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| No sidecar JSONs found | Prints "No input files found" and exits |
| Sidecar JSON exists but audio file missing | Skip with log |
| Sidecar JSON missing required fields | Skip with log (don't crash) |
| All files fail Stage 1 | Stages 2 and 3 run on zero files, outputs empty CSVs |
| One segment takes >60s for LID | Timeout, log, reject as `lid_timeout` |
| Pipeline interrupted (Ctrl+C) | Temp files remain. Next run resumes via caching. |
| Duplicate sidecar basenames in different source folders | OK — each is independent |
| Empty audio file (0 bytes) | Fails Stage 1, logged |
| Output directory has files from previous run | Append mode. Existing segment IDs are skipped. |

---

## Dependencies

```
transformers>=4.45.0
torch>=2.5.0
soundfile>=0.12.0
librosa>=0.10.0
pyyaml>=6.0
```

`ffmpeg` must be installed on the system.

---

<<<<<<< HEAD
=======
## Edge Cases

| Scenario | Behavior |
|---|---|
| No `manifest.yml` in input dir | Error, exit |
| Entry in `files` has no matching media file | Error, skip |
| Media file exists with no matching `files` entry | Skip with warning |
| `defaults` block omitted | Hardcoded fallback defaults applied |
| All files fail Stage 1 | Stages 2 and 3 run on zero files, outputs empty CSVs |
| One segment takes >60s for LID | Timeout, log, reject as `lid_timeout` |
| Pipeline interrupted (Ctrl+C) | Temp files remain (can inspect with `--keep-temp`) |
| Output directory has files from previous run | Auto-cleared before each run. Fresh output every time. |
| Empty audio file (0 bytes) | Fails Stage 1, logged |

---

>>>>>>> 68ebee6 (sync architecture doc with implemented pipeline)
## Deferred

| Item | Why |
|---|---|
| Streaming audio input (live radio) | Pipeline runs on files, not streams |
| Transcription | Pipeline is for dialect labeling, not ASR |
| VAD-based segmentation | Hard-cut approach chosen for simplicity |
| ONNX LID model | Added complexity; HF pipeline works |
| Dialect classification model | Pipeline output is training data FOR such models |
| Web UI for pipeline | CLI only |
| Multi-language support | Bikol-specific. Changing ISO codes changes language. |
