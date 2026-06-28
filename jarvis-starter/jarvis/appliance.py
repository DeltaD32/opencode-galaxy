"""One-command home appliance — bring up the whole offline JARVIS stack.

  python -m jarvis.appliance              # doctor preflight → gateway + voice daemons
  python -m jarvis.appliance --no-voice   # gateway only
  python -m jarvis.appliance --chat       # …then an interactive local request loop
  python -m jarvis.appliance --skip-doctor

Runs the home preflight (refuses to start if anything is non-local), launches the
gateway (read API for the galaxy) and the voice daemon as subprocesses, prints a
dashboard, and shuts them down cleanly on Ctrl+C. With --chat it also drives the
agent loop locally (orchestrator + your local LLM). Point the frontend at the gateway.
"""
from __future__ import annotations
import os, sys, signal, subprocess, time

# (app import path, port) for each long-running service.
GATEWAY = ("daemons.gateway.app:app", 8132)
VOICE = ("daemons.voice.app:app", 8131)


def uvicorn_cmd(app_path: str, port: int, python: str | None = None) -> list[str]:
    return [python or sys.executable, "-m", "uvicorn", app_path, "--port", str(port)]


def services(*, voice: bool = True):
    """The (name, app_path, port) tuples to launch."""
    svc = [("gateway", *GATEWAY)]
    if voice:
        svc.append(("voice", *VOICE))
    return svc


def preflight() -> bool:
    """Run the home doctor; True if the system is safe (fully local) to start."""
    from . import doctor
    return doctor.check()["ok"]


def start(*, voice: bool = True, skip_doctor: bool = False, _spawn=None, _preflight=None):
    """Launch the appliance services. Returns [(name, port, process)]. Pure
    orchestration — `_spawn` / `_preflight` are injectable for tests."""
    pf = _preflight or preflight
    if not skip_doctor and not pf():
        raise RuntimeError(
            "home preflight failed — run `python -m jarvis.doctor` and fix it, or pass --skip-doctor")
    spawn = _spawn or (lambda cmd: subprocess.Popen(cmd))
    return [(name, port, spawn(uvicorn_cmd(app_path, port)))
            for name, app_path, port in services(voice=voice)]


def _chat_loop(repo: str):
    """Interactive local request loop: text → plan → execute via the local LLM."""
    from . import orchestrator
    from .llm import complete
    print('Local chat — type a task, "exit" to quit.')
    while True:
        try:
            line = input("jarvis> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not line or line in {"exit", "quit"}:
            return
        try:
            res = orchestrator.handle_request(line, os.path.abspath(repo), complete, auto_approve=True)
            for t in res.get("tasks", []):
                print(f"  [{t['id']}] {t['agent']}: {t['status']}")
        except Exception as e:  # keep the loop alive on a bad turn
            print(f"  ! {type(e).__name__}: {e}")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="JARVIS home appliance launcher")
    ap.add_argument("--skip-doctor", action="store_true", help="bypass the home preflight")
    ap.add_argument("--no-voice", action="store_true", help="gateway only (no voice daemon)")
    ap.add_argument("--chat", action="store_true", help="also start an interactive local request loop")
    ap.add_argument("--repo", default=os.getcwd(), help="repo root for chat tasks")
    args = ap.parse_args(argv)

    try:
        procs = start(voice=not args.no_voice, skip_doctor=args.skip_doctor)
    except RuntimeError as e:
        print(f"✗ {e}")
        return 1

    print("\nJARVIS appliance — running locally:")
    for name, port, _p in procs:
        print(f"  • {name:8s} http://127.0.0.1:{port}")
    print("  • galaxy   frontend/  (npm run dev → http://localhost:5273, reads the gateway)")
    print('\nRequests:  python run.py --go "<task>"   (or --chat for an inline loop)')
    print("Ctrl+C to stop.\n")

    def _shutdown(*_):
        for _name, _port, p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    try:
        if args.chat:
            _chat_loop(args.repo)
            _shutdown()
        while True:
            time.sleep(1)
            for name, _port, p in procs:
                if p.poll() is not None:
                    print(f"✗ {name} exited ({p.returncode}); shutting down")
                    _shutdown()
    except KeyboardInterrupt:
        _shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
