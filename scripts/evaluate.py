"""Fixed development evaluation; preserves raw results for human review."""
import json
import time
from datetime import datetime, timezone
from japanese_learning.config import ROOT, MODEL_REVISION, PROMPT_VERSION
from japanese_learning.inference import LocalModel
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store
from japanese_learning.prompts import ASSESSOR, assessment_data
from japanese_learning.contracts import Assessment


def main():
    cases = json.loads((ROOT / "scripts" / "evaluation_cases.json").read_text(encoding="utf-8"))
    model = LocalModel()
    service = PracticeService(model, Store(ROOT / "outputs" / "evaluation.sqlite3"))
    rows = []
    folder = ROOT / "outputs" / "evaluation"
    folder.mkdir(parents=True, exist_ok=True)
    for case in cases:
        print("Evaluating " + case["id"], flush=True)
        started = time.perf_counter()
        try:
            result = service.evaluate_answer(case["source"], case["answer"], "N3")
            rows.append({**case, "feedback": result.model_dump(), "overall": result.overall, "metrics": model.last_metrics,
                         "total_seconds": time.perf_counter() - started})
        except Exception as exc:
            rows.append({**case, "error": str(exc)})
        (folder / "results.json").write_text(json.dumps({"model_revision": MODEL_REVISION, "prompt_version": PROMPT_VERSION,
            "run_at": datetime.now(timezone.utc).isoformat(), "cases": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    failures = []
    for row in rows:
        if "error" in row:
            failures.append(row["id"] + ": " + row["error"])
            continue
        if row["valid"]:
            if row["feedback"]["meaning"] < 9 or any(c["kind"] == "error" for c in row["feedback"]["corrections"]):
                failures.append(row["id"] + ": valid translation penalized; review needed")
        else:
            dimension = row.get("dimension", "meaning")
            peers = [r["feedback"][dimension] for r in rows if r["group"] == row["group"] and r["valid"] and "feedback" in r]
            if peers and row["feedback"][dimension] >= min(peers):
                failures.append(row["id"] + f": {dimension} error not below valid alternatives")
            if row["id"] == "instruction_only" and any(row["feedback"][d] != 0 for d in ("meaning", "grammar", "naturalness")):
                failures.append("instruction_only: non-translation did not receive zero scores")
    (folder / "gates.json").write_text(json.dumps({"failures": failures, "independent_review_recommended": True}, indent=2), encoding="utf-8")
    print(json.dumps({"cases": len(rows), "failures": failures}), flush=True)


if __name__ == "__main__":
    main()
