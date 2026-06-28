"""Eval-harness tests (Module D) — mock planner, no network."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import evals


def test_seed_cases_all_pass():
    cases = evals.load_cases()
    res = evals.run_evals(evals.make_mock_planner(cases), cases=cases, min_pass_rate=1.0)
    assert res["ok"] and res["pass_rate"] == 1.0, res
    assert res["passed"] == len(cases)
    print("  ✓ eval harness: seed cases pass at rate 1.0 with the bundled planner")


def test_wrong_expectation_is_reported_failed():
    cases = evals.load_cases()
    bad = [dict(cases[0])]
    bad[0]["expect"] = {"n_tasks": 99}  # impossible
    res = evals.run_evals(evals.make_mock_planner(cases), cases=bad, min_pass_rate=1.0)
    assert not res["ok"] and res["failed"] == 1, res
    assert any("n_tasks" in r for d in res["details"] for r in d["reasons"]), res
    print("  ✓ eval harness: a wrong expectation is reported as a failure (gate holds)")


if __name__ == "__main__":
    test_seed_cases_all_pass()
    test_wrong_expectation_is_reported_failed()
    print("\nEVAL HARNESS (Module D) TESTS PASSED ✅")
