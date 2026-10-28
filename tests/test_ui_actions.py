import json
from japanese_learning.storage import Store
from japanese_learning.service import PracticeService
from japanese_learning.ui_actions import Actions
from test_core import FakeModel, GOOD, ENGLISH, TARGETS


def test_failure_retains_exercise_and_answer(tmp_path):
    actions = Actions(PracticeService(FakeModel(RuntimeError("GPU unavailable")), Store(tmp_path / "db")))
    result = actions.generate("雨", "N3")
    assert all(value == {"__type__": "update"} for value in result[:4])
    assert "GPU unavailable" in result[4]
    assert result[5] == {"__type__": "update"}


def test_history_reopen_hides_previous_feedback(tmp_path):
    store = Store(tmp_path / "db")
    exercise = store.create_exercise(["rain"], "N3", ENGLISH)
    service = PracticeService(FakeModel(json.dumps(GOOD)), store)
    actions = Actions(service)
    assert "first" in actions.submit(None, "雨です。")[1]
    rendered, status = actions.submit(exercise["id"], "雨です。")
    assert "9.3" in rendered and "saved" in status
    key = store.history()[0]["attempt_id"]
    table, dropdown, _ = actions.refresh()
    assert len(table) == 1
    assert "Your answer" in actions.detail(key)
    reopened = actions.reopen(key)
    assert reopened[:4] == (exercise["id"], ENGLISH, "", "")
    assert reopened[6] == "N3"
    assert actions.retry(exercise["id"])[:2] == ("", "")


def test_unanswered_history_and_saved_failure(tmp_path):
    store = Store(tmp_path / "db")
    exercise = store.create_exercise(["rain"], "N3", ENGLISH)
    actions = Actions(PracticeService(FakeModel(RuntimeError("Out of memory")), store))
    assert actions.refresh()[0][0][4] == "unanswered"
    html, message = actions.submit(exercise["id"], "雨です。")
    assert html == "" and "remains" in message
    assert "Out of memory" in actions.detail(store.history()[0]["attempt_id"])


def test_japanese_targets_restored_on_reopen(tmp_path):
    store = Store(tmp_path / "db")
    exercise = store.create_exercise(["雨", "電車", "傘"], "N3", ENGLISH, targets=TARGETS)
    actions = Actions(PracticeService(FakeModel(), store))
    key = "exercise:" + exercise["id"]
    assert actions.reopen(key)[5] == "雨、電車、傘"
    assert actions.reopen(key)[8] == "雨、電車、傘"
    assert "Japanese target vocabulary" in actions.detail(key)
    assert actions.refresh()[0][0][2] == "雨、電車、傘"


def test_legacy_exercise_remains_usable_with_empty_japanese_input(tmp_path):
    store = Store(tmp_path / "db")
    ex = store.create_exercise(["rain"], "N3", ENGLISH)
    actions = Actions(PracticeService(FakeModel(), store))
    reopened = actions.reopen("exercise:" + ex["id"])
    assert reopened[0] == ex["id"] and reopened[5] == ""
    assert "Legacy" in reopened[4]
