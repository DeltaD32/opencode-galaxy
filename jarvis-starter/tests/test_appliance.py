"""Appliance launcher tests — command construction + doctor gate (no real servers)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import appliance


class _FakeProc:
    returncode = None
    def poll(self):
        return None
    def terminate(self):
        pass


def test_uvicorn_cmd_and_services():
    assert appliance.uvicorn_cmd("daemons.gateway.app:app", 8132, python="py") == \
        ["py", "-m", "uvicorn", "daemons.gateway.app:app", "--port", "8132"]
    assert [s[0] for s in appliance.services(voice=True)] == ["gateway", "voice"]
    assert [s[0] for s in appliance.services(voice=False)] == ["gateway"]
    print("  ✓ uvicorn command + service list are correct (gateway + voice)")


def test_start_is_gated_by_doctor():
    spawned = []
    spawn = lambda cmd: (spawned.append(cmd) or _FakeProc())

    # doctor fails → start refuses; nothing is launched
    try:
        appliance.start(_spawn=spawn, _preflight=lambda: False)
        assert False, "should refuse to start when preflight fails"
    except RuntimeError:
        pass
    assert spawned == []

    # doctor ok → gateway + voice launched
    procs = appliance.start(_spawn=spawn, _preflight=lambda: True)
    assert len(procs) == 2 and len(spawned) == 2
    assert {p[0] for p in procs} == {"gateway", "voice"}
    print("  ✓ start() refuses when the home preflight fails, launches both when it passes")


def test_skip_doctor_bypasses_preflight():
    spawned = []
    spawn = lambda cmd: (spawned.append(cmd) or _FakeProc())

    def _must_not_run():
        raise AssertionError("preflight must not be called with --skip-doctor")

    procs = appliance.start(voice=False, skip_doctor=True, _spawn=spawn, _preflight=_must_not_run)
    assert len(procs) == 1 and procs[0][0] == "gateway"
    print("  ✓ --skip-doctor bypasses preflight and starts the gateway only")


if __name__ == "__main__":
    test_uvicorn_cmd_and_services()
    test_start_is_gated_by_doctor()
    test_skip_doctor_bypasses_preflight()
    print("\nAPPLIANCE TESTS PASSED ✅")
