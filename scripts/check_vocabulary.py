"""Real-model checks for focused Japanese vocabulary feedback."""
import json
from japanese_learning.config import ROOT, PROMPT_VERSION
from japanese_learning.inference import LocalModel
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store

CASES = [
    ("conjugation", "I ate dinner at home last night.", "昨夜、家で夕食を食べました。", "食べる", "eat", True),
    ("kana", "I went to the library yesterday.", "きのう、としょかんにいきました。", "図書館", "library", True),
    ("synonym", "I ate dinner at home last night.", "昨夜、家で夕食をいただきました。", "食べる", "eat", False),
    ("adjective", "The library is quiet, so I read a book there every afternoon.", "図書館は静かなので、毎日午後にそこで本を読みます。", "静か", "quiet", True),
    ("missing", "I took an umbrella to the station.", "駅に行きました。", "傘", "umbrella", False),
]

model = LocalModel()
service = PracticeService(model, Store(ROOT / "outputs" / "vocabulary_check.sqlite3"))
results = []
for name, source, answer, word, meaning, expected in CASES:
    try:
        result = service.evaluate_answer(source, answer, "N3", [{"word": word, "english": meaning}])
        passed = result.vocabulary_usage[0].used == expected
        if name in ("conjugation", "kana", "synonym", "adjective"):
            passed = passed and result.meaning >= 9
        results.append({"id": name, "source": source, "answer": answer, "expected_use": expected,
                        "passed": passed, "feedback": result.model_dump(), "metrics": model.last_metrics})
    except Exception as exc:
        results.append({"id": name, "passed": False, "error": str(exc)})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    (ROOT / "outputs" / "vocabulary_check_results.json").write_text(json.dumps(
        {"prompt_version": PROMPT_VERSION, "cases": results}, ensure_ascii=False, indent=2), encoding="utf-8")
if not all(item["passed"] for item in results):
    raise SystemExit("Vocabulary quality checks failed; inspect outputs/vocabulary_check_results.json")
