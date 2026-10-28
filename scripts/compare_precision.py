"""Focused precision investigation after a failed semantic-role quality gate."""
import json
from japanese_learning.config import ROOT, MODEL_REVISION, PROMPT_VERSION
from japanese_learning.inference import LocalModel
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store
from japanese_learning.prompts import ASSESSOR, assessment_data
from japanese_learning.contracts import Assessment


def main():
    model = LocalModel(bits=8)
    service = PracticeService(model, Store(ROOT / "outputs" / "precision.sqlite3"))
    cases = json.loads((ROOT / "scripts" / "evaluation_cases.json").read_text(encoding="utf-8"))
    cases = [case for case in cases if case["id"] in ("particle_good", "particle_bad", "tense", "kana")]
    results = []
    for case in cases:
        result = service.structured(ASSESSOR, assessment_data(case["source"], case["answer"], "N3"), Assessment, "precision8")
        results.append({**case, "feedback": result.model_dump(), "metrics": model.last_metrics})
        print(case["id"], result.model_dump_json(), flush=True)
    (ROOT / "outputs" / "precision8_results.json").write_text(json.dumps(
        {"model_revision": MODEL_REVISION, "prompt_version": PROMPT_VERSION, "bits": 8, "cases": results},
        ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
