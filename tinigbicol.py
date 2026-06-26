#!/usr/bin/env python3
"""tinigbicol — centralized entry point for pipeline CLI and dashboard server.

usage:
  tinigbicol pipeline <input_dir> <output_dir> [--skip-classify] [--keep-temp] [-v]
  tinigbicol serve [--port PORT] [--no-frontend]
  tinigbicol -h | --help
"""

import argparse
import os
import signal
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def cmd_pipeline():
    sys.argv.pop(1)
    sys.path.insert(0, os.path.join(ROOT, "pipeline"))
    import run
    run.main()


def cmd_serve(args: argparse.Namespace):
    backend_dir = os.path.join(ROOT, "web_app", "backend")
    frontend_dir = os.path.join(ROOT, "web_app", "frontend")

    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)

    from uvicorn import run as uvicorn_run

    children: list[subprocess.Popen] = []

    def kill_children(*_):
        for child in children:
            try:
                if os.name == "nt":
                    child.terminate()
                else:
                    os.killpg(os.getpgid(child.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        sys.exit(0)

    if not args.no_frontend:
        kwargs: dict = {}
        if os.name != "nt":
            kwargs["preexec_fn"] = os.setsid
        p = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            **kwargs,
        )
        children.append(p)
        print("  Frontend: http://localhost:3000")

    if os.name != "nt":
        signal.signal(signal.SIGINT, kill_children)
        signal.signal(signal.SIGTERM, kill_children)

    print(f"  Backend:  http://localhost:{args.port}")
    print("  Press Ctrl+C to stop\n")

    try:
        uvicorn_run("app.main:app", host="0.0.0.0", port=args.port, reload=True)
    finally:
        kill_children()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "pipeline":
        cmd_pipeline()
    elif cmd == "serve":
        parser = argparse.ArgumentParser(prog="tinigbicol serve", add_help=False)
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--no-frontend", action="store_true")
        parser.add_argument("-h", "--help", action="store_true")
        args = parser.parse_args(sys.argv[2:])
        if args.help:
            print("usage: tinigbicol serve [options]\n")
            print("options:")
            print("  --port PORT      Backend port (default: 8000)")
            print("  --no-frontend    Skip frontend dev server")
            print("  -h, --help       Show this help")
            return
        cmd_serve(args)
    else:
        print(f"Unknown command: {cmd}\n")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
