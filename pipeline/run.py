import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from pipeline.config import MODEL_CACHE_DIR
from pipeline.manifest import load_manifest
from pipeline.normalize import normalize
from pipeline.output import OutputWriter
from pipeline.segment import get_duration_ms, segment


def main():
    parser = argparse.ArgumentParser(description="Bikol Speech Preprocessing Pipeline")
    parser.add_argument("input_dir", type=Path, help="Directory with manifest.yml + media files")
    parser.add_argument("output_dir", type=Path, help="Directory to write output")
    parser.add_argument("--skip-validate", action="store_true", help="Skip Stage 3 (Bikol validation)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files for debugging")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print per-file progress")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.is_dir():
        print(f"Error: input directory not found: {input_dir}")
        sys.exit(1)

    entries = load_manifest(input_dir)
    temp_dir = Path(tempfile.mkdtemp(prefix="pipeline_"))
    output = OutputWriter(output_dir)

    total = len(entries)
    print(f"\n{'='*50}")
    print(f"  Bikol Speech Preprocessing Pipeline")
    print(f"{'='*50}")
    print(f"\nInput files: {total}")

    # --- Stage 1: Normalize ---
    norm_ok = 0
    norm_fail = 0
    normalized = []

    for i, entry in enumerate(entries):
        if args.verbose:
            print(f"  [{i+1}/{total}] {entry['_basename']} — normalizing...")
        wav = normalize(entry["_input_path"], entry["_basename"], temp_dir)
        if wav:
            normalized.append((entry, wav))
            norm_ok += 1
            output.log("normalize", entry["_basename"], "ok", output=str(wav))
        else:
            norm_fail += 1
            output.log("normalize", entry["_basename"], "fail", error="ffmpeg_fail")

    print(f"  Stage 1 (normalize):  {norm_ok} ok, {norm_fail} failed")

    # --- Stage 2: Segment ---
    seg_count = 0
    segments = []

    for entry, wav in normalized:
        seg_config = entry.get("segment", {})
        segs = segment(wav, seg_config, temp_dir)

        if args.verbose:
            print(f"  {entry['_basename']} → {len(segs)} segments")

        for seg in segs:
            segments.append((entry, seg))
            seg_count += 1

        output.log("segment", entry["_basename"], "ok",
                   input_duration_ms=get_duration_ms(wav),
                   segments=len(segs))

    print(f"  Stage 2 (segment):   {seg_count} segments")

    # --- Stage 3: Validate ---
    kept = 0
    rejected = 0

    if args.skip_validate:
        print(f"  Stage 3 (validate):  SKIPPED (--skip-validate)")
        print(f"\n  Tip: Run validation in Colab:\n"
              f"    → Open pipeline/validate.ipynb\n"
              f"    → Upload {output_dir}/audio/ as a zip\n"
              f"    → Runtime → Run All")
    elif segments:
        print(f"  Stage 3 (validate):  loading model...")
        from pipeline.validate import load_model, validate

        model = load_model(MODEL_CACHE_DIR)

        reject_reasons = {}
        for entry, seg in segments:
            validate_config = entry.get("validate", {})
            result = validate(model, seg, validate_config)

            dur = get_duration_ms(seg)

            if result["status"] == "keep":
                output.add_manifest_row(entry, seg, result["top_lang"], result["score"], dur)
                kept += 1
            else:
                reason = result.get("reason", "unknown")
                reject_reasons[reason] = reject_reasons.get(reason, 0) + 1
                output.add_rejected_row(entry, seg, reason,
                                        lang=result.get("top_lang", ""),
                                        score=result.get("score", 0.0),
                                        duration_ms=dur)
                rejected += 1

            log_result = dict(result)
            log_result.pop("status")
            output.log("validate", seg.stem, result["status"], **log_result)

            if args.verbose:
                status = "\u2713" if result["status"] == "keep" else "\u2717"
                print(f"  {status} {seg.stem}: {result.get('top_lang','?')} ({result.get('score',0):.3f})")

        print(f"  Stage 3 (validate):  {kept} kept, {rejected} rejected")

        if reject_reasons:
            print(f"\n  Reject reasons:")
            for reason, count in sorted(reject_reasons.items(), key=lambda x: -x[1]):
                print(f"    {reason:20s}: {count}")

    # --- Write outputs ---
    output.write()

    print(f"\nOutput:")
    print(f"  {output_dir}/audio/     : {kept} segments")
    if rejected:
        print(f"  {output_dir}/rejected/  : {rejected} segments")
    if output._manifest_rows:
        print(f"  {output_dir}/manifest.csv  : {len(output._manifest_rows)} rows")
    if output._rejected_rows:
        print(f"  {output_dir}/rejected.csv  : {len(output._rejected_rows)} rows")
    print(f"  {output_dir}/pipeline.log   : {output._log_path.stat().st_size if output._log_path.exists() else '?'} bytes")

    # Cleanup
    if not args.keep_temp:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\nDone.")


if __name__ == "__main__":
    main()
