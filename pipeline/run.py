import argparse
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from pipeline.config import MODEL_CACHE_DIR
from pipeline.manifest import load_manifest
from pipeline.normalize import normalize
from pipeline.output import OutputWriter
from pipeline.segment import get_duration_ms, segment

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _fmt(s, color):
    return f"{color}{s}{RESET}"


def main():
    parser = argparse.ArgumentParser(description="Bikol Speech Preprocessing Pipeline")
    parser.add_argument("input_dir", type=Path, help="Directory with manifest.yml + media files")
    parser.add_argument("output_dir", type=Path, help="Directory to write output")
    parser.add_argument("--skip-classify", action="store_true", help="Skip Stage 3 (language classification)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files for debugging")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show per-segment classification results")
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
    start = time.time()

    print(f"\n  {_fmt(input_dir.name + '/', BOLD)}→ {total} file{'s' if total != 1 else ''}")
    print(f"  {_fmt('─' * 66, DIM)}")
    print()

    norm_ok = norm_fail = 0
    seg_files = seg_count = 0
    kept = rejected = 0
    reject_reasons: dict[str, int] = defaultdict(int)

    model = None
    if not args.skip_classify:
        from pipeline.validate import load_model, classify
        model = load_model(MODEL_CACHE_DIR)
        if args.verbose:
            print()

    for entry in entries:
        basename = entry["_basename"]
        norm_status = seg_status = classify_status = ""
        file_kept = file_rejected = 0
        file_langs: dict[str, int] = defaultdict(int)

        # ── Stage 1: Normalize ──
        wav = normalize(entry["_input_path"], basename, temp_dir)
        if wav:
            norm_ok += 1
            norm_status = _fmt("norm", GREEN)
        else:
            norm_fail += 1
            norm_status = _fmt("norm", RED)
            output.log("normalize", basename, "fail", error="ffmpeg_fail")
            line = f"  {basename:<28s}  {norm_status:<6s}  {_fmt('failed', RED)}"
            print(line)
            continue

        output.log("normalize", basename, "ok", output=str(wav))

        # ── Stage 2: Segment ──
        seg_config = entry.get("segment", {})
        segs = segment(wav, seg_config, temp_dir)
        output.log("segment", basename, "ok",
                   input_duration_ms=get_duration_ms(wav),
                   segments=len(segs))

        if not segs:
            seg_status = _fmt("seg", YELLOW)
            line = f"  {basename:<28s}  {norm_status:<6s}  {seg_status:<8s}  {_fmt('no segments', YELLOW)}"
            print(line)
            continue

        seg_files += 1
        seg_count += len(segs)
        seg_status = _fmt(f"seg({len(segs)})", GREEN)

        # ── Stage 3: Classify ──
        if args.skip_classify:
            for seg in segs:
                dur = get_duration_ms(seg)
                output.add_row(entry, seg, "", 0.0, dur)
                kept += 1
            classify_status = _fmt("skip-classify", YELLOW)
        else:
            for seg in segs:
                result = classify(model, seg)
                dur = get_duration_ms(seg)
                file_langs[result["lang"]] += 1

                if result["is_ph"]:
                    output.add_row(entry, seg, result["lang"], result["score"], dur)
                    file_kept += 1
                else:
                    lang = result["lang"] or "unknown"
                    reason = "lid_error" if not result["lang"] else "not_ph_language"
                    reject_reasons[reason] += 1
                    output.add_rejected_row(entry, seg, reason,
                                            lang=result["lang"],
                                            score=result["score"],
                                            duration_ms=dur)
                    file_rejected += 1

                output.log("classify", seg.stem, "keep" if result["is_ph"] else "reject",
                           lang=result["lang"], score=result["score"])

                if args.verbose:
                    status = _fmt("✓", GREEN) if result["is_ph"] else _fmt("✗", RED)
                    lang_str = result["lang"] or "?"
                    print(f"  {'':28s}  {'':6s}  {'':8s}  {status}  {lang_str}  ({result['score']:.3f})")

            kept += file_kept
            rejected += file_rejected

            if file_kept > 0 and file_rejected == 0:
                top_lang = max(file_langs, key=file_langs.get) if file_langs else ""
                classify_status = _fmt(f"{file_kept} kept", GREEN)
                if top_lang:
                    classify_status += f"  ({top_lang})"
            elif file_rejected > 0 and file_kept == 0:
                classify_status = _fmt(f"{file_rejected} rejected", RED)
            else:
                classify_status = f"{_fmt(str(file_kept) + ' kept', GREEN)} / {_fmt(str(file_rejected) + ' rejected', RED)}"

        # ── Print per-file line ──
        line = f"  {basename:<28s}  {norm_status:<6s}  {seg_status:<10s}  {classify_status}"
        print(line)

    # ── Summary ──
    print()
    print(f"  {_fmt('─' * 66, DIM)}")

    norm_line = f"  normalize    {_fmt(f'{norm_ok} ok', GREEN)}    {_fmt(f'{norm_fail} fail', RED) if norm_fail else _fmt('0 fail', DIM)}"
    print(norm_line)

    seg_line = f"  segment      {seg_files} files  →  {seg_count} segment{'s' if seg_count != 1 else ''}"
    print(seg_line)

    if not args.skip_classify:
        cls_line = f"  classify     {_fmt(f'{kept} kept', GREEN)}    {_fmt(f'{rejected} rejected', RED) if rejected else _fmt('0 rejected', DIM)}"
        print(cls_line)
        if reject_reasons:
            for reason, count in sorted(reject_reasons.items(), key=lambda x: -x[1]):
                print(f"    {reason:<20s}  {count}")
    else:
        print(f"  classify     {_fmt('skipped (--skip-classify)', YELLOW)}")

    # ── Footer ──
    elapsed = time.time() - start
    if elapsed >= 60:
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
    else:
        elapsed_str = f"{elapsed:.1f}s"

    device = ""
    if not args.skip_classify:
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        except ImportError:
            device = "?"

    print()
    print(f"  runtime      {elapsed_str}", end="")
    if device:
        print(f"  |  {device.upper()}")
    else:
        print()
    print(f"  output       {output_dir}/")
    print(f"  {_fmt('─' * 66, DIM)}")
    print()

    if not args.keep_temp:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
