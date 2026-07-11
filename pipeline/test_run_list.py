"""Tests for the run-list CLI subcommand (subprocess, isolated artifacts root)."""
import json
import os
import subprocess
import sys
import tempfile
import shutil

CLI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_cli.py")


def _run(args, root):
    env = dict(os.environ, PIPELINE_ARTIFACTS_ROOT=root)
    return subprocess.run([sys.executable, CLI, *args], capture_output=True, text=True, env=env)


# AC1: empty store lists zero runs
def test_ac1_empty():
    root = tempfile.mkdtemp()
    try:
        d = json.loads(_run(["run-list"], root).stdout)
        assert d["count"] == 0 and d["runs"] == []
    finally:
        shutil.rmtree(root)


# AC2: created runs are listed with the right fields
def test_ac2_lists_created():
    root = tempfile.mkdtemp()
    try:
        rid = json.loads(_run(["run-create", "--project", "p", "--requirement", "x",
                               "--profile", "trivial"], root).stdout)["run_id"]
        d = json.loads(_run(["run-list"], root).stdout)
        assert d["count"] == 1
        row = d["runs"][0]
        assert row["run_id"] == rid and row["profile"] == "trivial"
        assert row["project"] == "p"          # Gate 2 LOW#4: pin the project field too
        assert row["status"] == "in_progress" and row["current_stage"] == "evaluate"
        assert row["stages_completed"] == 0
    finally:
        shutil.rmtree(root)


# Gate 2 HIGH/MED: a corrupt or non-dict run.json must NOT crash the whole listing
def test_adv_malformed_run_is_isolated():
    root = tempfile.mkdtemp()
    try:
        good = json.loads(_run(["run-create", "--project", "p", "--requirement", "x",
                                "--profile", "trivial"], root).stdout)["run_id"]
        os.makedirs(os.path.join(root, "runs", "run_bad"), exist_ok=True)
        with open(os.path.join(root, "runs", "run_bad", "run.json"), "w") as f:
            f.write("{ this is not json")          # truncated / corrupt
        os.makedirs(os.path.join(root, "runs", "run_list_typed"), exist_ok=True)
        with open(os.path.join(root, "runs", "run_list_typed", "run.json"), "w") as f:
            f.write("[]")                           # valid JSON but wrong type
        res = _run(["run-list"], root)
        assert res.returncode == 0, "must not crash on corrupt run.json"
        d = json.loads(res.stdout)
        ids = {r["run_id"]: r for r in d["runs"]}
        assert good in ids and ids[good]["status"] == "in_progress"   # healthy still listed
        assert ids["run_bad"].get("malformed") is True                # corrupt flagged, not fatal
        assert ids["run_list_typed"].get("malformed") is True         # non-dict flagged
    finally:
        shutil.rmtree(root)


# Gate 2 LOW#3: invalid --status is rejected by argparse (exit 2), not silently count=0
def test_adv_status_choices_enforced():
    root = tempfile.mkdtemp()
    try:
        res = _run(["run-list", "--status", "in-progress"], root)   # hyphen typo
        assert res.returncode == 2
    finally:
        shutil.rmtree(root)


# AC3: --status filter includes matches and excludes non-matches (both sides pinned)
def test_ac3_status_filter():
    root = tempfile.mkdtemp()
    try:
        _run(["run-create", "--project", "p", "--requirement", "x", "--profile", "trivial"], root)
        assert json.loads(_run(["run-list", "--status", "in_progress"], root).stdout)["count"] == 1
        assert json.loads(_run(["run-list", "--status", "completed"], root).stdout)["count"] == 0
    finally:
        shutil.rmtree(root)
