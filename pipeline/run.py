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
    parser.add_argument("--skip-classify", action="store_true", help="Skip Stage 3 (language classification)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files for debugging")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print per-file progress")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

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

    print(f"  Stage 1 (normalize):    {norm_ok} ok, {norm_fail} failed")

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

    print(f"  Stage 2 (segment):     {seg_count} segments")

    # --- Stage 3: Classify ---
    kept = 0
    rejected = 0

    if args.skip_classify:
        print(f"  Stage 3 (classify):    SKIPPED (--skip-classify)")
        print(f"\n  Tip: Run classification in Colab:\n"
              f"    → Open pipeline/validate.ipynb\n"
              f"    → Upload {output_dir}/audio/ as a zip\n"
              f"    → Runtime → Run All")
    elif segments:
        print(f"  Stage 3 (classify):    loading model...")
        from pipeline.validate import load_model, classify

        model = load_model(MODEL_CACHE_DIR)

        reject_reasons = {}
        for entry, seg in segments:
            result = classify(model, seg)
            dur = get_duration_ms(seg)

            if result["is_ph"]:
                output.add_row(entry, seg, result["lang"], result["score"], dur)
                kept += 1
            else:
                lang = result["lang"] or "unknown"
                reason = "lid_error" if not result["lang"] else f"not_ph_language"
                reject_reasons[reason] = reject_reasons.get(reason, 0) + 1
                output.add_rejected_row(entry, seg, reason,
                                        lang=result["lang"],
                                        score=result["score"],
                                        duration_ms=dur)
                rejected += 1

            output.log("classify", seg.stem, "keep" if result["is_ph"] else "reject",
                       lang=result["lang"], score=result["score"])

            if args.verbose:
                status = "\u2713" if result["is_ph"] else "\u2717"
                lang_str = result["lang"] or "?"
                print(f"  {status} {seg.stem}: {lang_str} ({result['score']:.3f})")

        print(f"  Stage 3 (classify):    {kept} kept, {rejected} rejected")

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
    if output._log_path.exists():
        print(f"  {output_dir}/pipeline.log   : {output._log_path.stat().st_size} bytes")

    if not args.keep_temp:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\nDone.")


if __name__ == "__main__":
    main()
