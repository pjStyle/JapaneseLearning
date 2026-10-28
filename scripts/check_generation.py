"""Exercise generation constraints and variety against the real local model."""
import json
from japanese_learning.config import ROOT, PROMPT_VERSION
from japanese_learning.inference import LocalModel
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store

model = LocalModel()
service = PracticeService(model, Store(ROOT / "outputs" / "generation.sqlite3"))
results = []
for words, level in [("コーヒー、本", "N4"), ("コーヒー、本", "N4"),
                     ("雨、電車、傘", "N3"), ("走る", "N4"), ("静か、図書館", "N3")]:
    try:
        exercise = service.generate(words, level)
        results.append({"words": words, "level": level, "english": exercise["english"], "targets": json.loads(exercise["targets"]), "metrics": model.last_metrics})
    except Exception as exc:
        results.append({"words": words, "level": level, "error": str(exc)})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
(ROOT / "outputs" / "japanese_generation_results.json").write_text(json.dumps(
    {"prompt_version": PROMPT_VERSION, "cases": results}, ensure_ascii=False, indent=2), encoding="utf-8")
