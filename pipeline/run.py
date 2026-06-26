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


def _relative(p: Path) -> str:
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)


def _truncate(name: str, width: int) -> str:
    if len(name) <= width:
        return name.ljust(width)
    return name[: width - 3] + "..."


def _duration_str(ms: int) -> str:
    s = ms / 1000
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"


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
    counter_width = len(f"[{total}/{total}]") + 1
    start = time.time()

    # ── Header ──
    print(f"\n  {_fmt('Bikol Speech Pipeline', BOLD)}")
    print(f"  {_fmt('─' * 72, DIM)}")
    print(f"  input   {_relative(input_dir)}/  ({total} file{'s' if total != 1 else ''})")
    print(f"  output  {_relative(output_dir)}/")
    print(f"  {_fmt('─' * 72, DIM)}")
    print(f"  {'':{counter_width}s}  {'FILE':<26s}  STAGE 1   STAGE 2      RESULT")
    print(f"  {_fmt('─' * 72, DIM)}")

    # ── Stats ──
    norm_ok = norm_fail = 0
    seg_files = seg_count = 0
    kept = rejected = 0
    total_duration_ms = 0
    lang_distro: dict[str, int] = defaultdict(int)
    dialect_distro: dict[str, int] = defaultdict(int)
    reject_reasons: dict[str, int] = defaultdict(int)

    # ── Load model ──
    model = None
    if not args.skip_classify:
        from pipeline.validate import load_model, classify
        model = load_model(MODEL_CACHE_DIR)

    # ── Per-file loop ──
    for i, entry in enumerate(entries, 1):
        ext = entry["_input_path"].suffix
        basename = entry["_basename"]
        full_name = basename + ext
        display_name = _truncate(full_name, 26)
        file_langs: dict[str, int] = defaultdict(int)
        counter = f"[{i}/{total}]"
        norm_str = seg_str = result_str = ""
        file_kept = file_rejected = 0

        # Stage 1
        wav = normalize(entry["_input_path"], basename, temp_dir)
        if wav:
            norm_ok += 1
            norm_str = _fmt("norm", GREEN)
        else:
            norm_fail += 1
            norm_str = _fmt("norm", RED)
            output.log("normalize", basename, "fail", error="ffmpeg_fail")
            result_str = _fmt("failed", RED)
            print(f"  {counter:<{counter_width}s}  {display_name:<26s}  {norm_str:<8s}  {'':<12s}  {result_str}")
            continue

        output.log("normalize", basename, "ok", output=str(wav))

        # Stage 2
        seg_config = entry.get("segment", {})
        segs = segment(wav, seg_config, temp_dir)
        output.log("segment", basename, "ok",
                   input_duration_ms=get_duration_ms(wav),
                   segments=len(segs))

        if not segs:
            seg_str = _fmt("seg", YELLOW)
            result_str = _fmt("no segments", YELLOW)
            print(f"  {counter:<{counter_width}s}  {display_name:<26s}  {norm_str:<8s}  {seg_str:<12s}  {result_str}")
            continue

        seg_files += 1
        seg_count += len(segs)
        seg_str = _fmt(f"seg({len(segs)})", GREEN)

        # Stage 3
        if args.skip_classify:
            for seg in segs:
                dur = get_duration_ms(seg)
                total_duration_ms += dur
                dialect_distro[entry.get("dialect_label", "unknown")] += 1
                output.add_row(entry, seg, "", 0.0, dur)
                kept += 1
            result_str = _fmt("skip", YELLOW)
        else:
            for seg in segs:
                result = classify(model, seg)
                dur = get_duration_ms(seg)
                total_duration_ms += dur
                lang_distro[result["lang"]] += 1
                dialect_distro[entry.get("dialect_label", "unknown")] += 1

                if result["is_ph"]:
                    file_langs[result["lang"]] += 1
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
                    s = _fmt("✓", GREEN) if result["is_ph"] else _fmt("✗", RED)
                    ls = result["lang"] or "?"
                    pad = counter_width + 2
                    print(f"  {'':{pad}s}  {'':26s}  {'':8s}  {'':12s}  {s}  {ls}  ({result['score']:.3f})")

            kept += file_kept
            rejected += file_rejected

            if file_kept > 0 and file_rejected == 0:
                top = max(file_langs, key=file_langs.get) if file_langs else ""
                result_str = _fmt(f"{file_kept} kept", GREEN)
                if top:
                    result_str += f"  ({top})"
            elif file_rejected > 0 and file_kept == 0:
                result_str = _fmt(f"{file_rejected} rejected", RED)
            else:
                result_str = f"{_fmt(str(file_kept) + ' kept', GREEN)}/{_fmt(str(file_rejected) + ' rej', RED)}"

        print(f"  {counter:<{counter_width}s}  {display_name:<26s}  {norm_str:<8s}  {seg_str:<12s}  {result_str}")

    # ── Summary ──
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
    print(f"  {_fmt('─' * 72, DIM)}")
    print(f"  {_fmt('Summary', BOLD)}")
    print(f"  {_fmt('─' * 72, DIM)}")

    n_ok = _fmt(f"{norm_ok} ok", GREEN) if norm_ok > 0 else _fmt("0 ok", DIM)
    n_fail = _fmt(f"{norm_fail} fail", RED) if norm_fail > 0 else _fmt("0 fail", DIM)
    print(f"  normalize    {n_ok}    {n_fail}")

    print(f"  segment      {seg_files} file{'s' if seg_files != 1 else ''}  "
          f"→  {seg_count} segment{'s' if seg_count != 1 else ''}  "
          f"({_duration_str(total_duration_ms)} total)")

    if not args.skip_classify:
        k = _fmt(f"{kept} kept", GREEN) if kept > 0 else _fmt("0 kept", DIM)
        r = _fmt(f"{rejected} rejected", RED) if rejected > 0 else _fmt("0 rejected", DIM)
        print(f"  classify      {k}    {r}")

        if lang_distro:
            sorted_langs = sorted(lang_distro.items(), key=lambda x: -x[1])
            lang_strs = [f"{_fmt(lang, CYAN)}: {count}" for lang, count in sorted_langs]
            print(f"  languages     {'  '.join(lang_strs)}")

        if reject_reasons:
            r_strs = [f"{reason}: {count}" for reason, count in sorted(reject_reasons.items(), key=lambda x: -x[1])]
            print(f"  rejections    {'  '.join(r_strs)}")
    else:
        print(f"  classify      {_fmt('skipped', YELLOW)}")

    if dialect_distro:
        sorted_dialects = sorted(dialect_distro.items(), key=lambda x: -x[1])
        d_strs = [f"{_fmt(d, CYAN)}: {count}" for d, count in sorted_dialects]
        print(f"  dialects      {'  '.join(d_strs)}")

    # ── Footer ──
    print(f"  {_fmt('─' * 72, DIM)}")
    done = _fmt("✓ Pipeline complete", GREEN)
    output_rel = _relative(output_dir)
    dev = f"  {device.upper()}" if device else ""
    print(f"  {done}   {elapsed_str}{dev}  →  {output_rel}/")
    print(f"  {_fmt('─' * 72, DIM)}")
    print()

    if not args.keep_temp:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
