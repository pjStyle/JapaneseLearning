"""Run before UI work to validate the actual Windows/GPU backend."""
import json
import time
from japanese_learning.inference import LocalModel
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store
from japanese_learning.config import ROOT

model = LocalModel()
service = PracticeService(model, Store(ROOT / "outputs" / "smoke.sqlite3"))
started = time.perf_counter()
exercise = service.generate("雨、電車、傘", "N3")
print(json.dumps(exercise, ensure_ascii=False), flush=True)
result = service.assess(exercise["id"], "雨が降っていたので、傘を持って電車で駅に行きました。")
print(result.model_dump_json(indent=2), flush=True)
(ROOT / "outputs" / "smoke_result.json").write_text(json.dumps(
    {"exercise": exercise, "assessment": result.model_dump(), "total_seconds": time.perf_counter() - started},
    ensure_ascii=False, indent=2), encoding="utf-8")
