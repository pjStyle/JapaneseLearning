import json
import sqlite3
import pytest
from japanese_learning.contracts import Assessment, ExerciseResult
from japanese_learning.presentation import feedback_html
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store
from test_core import ENGLISH, GOOD, TARGETS, FakeModel


def test_meanings_must_cover_the_requested_japanese_words():
    for targets in ([], TARGETS[:2], TARGETS[::-1], [{"word": "本", "english": "book"}]):
        with pytest.raises(ValueError):
            ExerciseResult(english=ENGLISH, targets=targets).check(["雨", "電車", "傘"])
    with pytest.raises(ValueError):
        ExerciseResult(english=ENGLISH, targets=[{"word": "傘", "english": "parasol"}]).check(["傘"])


def test_coverage_is_validated_and_separate_from_scores(tmp_path):
    targets = [{"word": "食べる", "english": "eat"}]
    result = {**GOOD, "meaning": 10, "grammar": 10, "naturalness": 10,
              "vocabulary_usage": [{"word": "食べる", "used": False, "note": "A valid synonym was used; practise 食べる next time."}]}
    service = PracticeService(FakeModel(json.dumps(result)), Store(tmp_path / "db"))
    feedback = service.evaluate_answer("I eat dinner at home.", "家で夕食をいただきます。", "N3", targets)
    assert feedback.overall == 10 and not feedback.vocabulary_usage[0].used
    assert "Not used" in feedback_html(feedback)
    with pytest.raises(ValueError):
        Assessment(**GOOD).check_targets(targets)


def test_bad_coverage_gets_one_repair(tmp_path):
    wrong = {**GOOD, "vocabulary_usage": [{"word": "本", "used": True, "note": "Wrong target."}]}
    correct = {**GOOD, "vocabulary_usage": [{"word": "食べる", "used": True, "note": "食べました is a conjugation of 食べる."}]}
    service = PracticeService(FakeModel(json.dumps(wrong), json.dumps(correct)), Store(tmp_path / "db"))
    result = service.evaluate_answer("I ate dinner.", "夕食を食べました。", "N3", [{"word": "食べる", "english": "eat"}])
    assert result.vocabulary_usage[0].used
    assert len(service.model.calls) == 3


def test_existing_database_migration_keeps_history(tmp_path):
    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE exercises (id TEXT PRIMARY KEY,created_at TEXT,words TEXT,level TEXT,english TEXT,model_revision TEXT,prompt_version TEXT)")
        db.execute("INSERT INTO exercises VALUES (?,?,?,?,?,?,?)", ("old", "2026-10-28T00:00:00+00:00", '["rain"]', "N3", ENGLISH, "rev", "7"))
    store = Store(path)
    row = store.exercise("old")
    assert row["input_language"] == "en" and row["targets"] == "[]"
    assert row["english"] == ENGLISH and len(store.history()) == 1
    assert Store(path).exercise("old") == row  # Migration is repeatable.
