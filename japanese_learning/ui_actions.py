import json
import logging
from datetime import datetime, timedelta, timezone
from html import escape
import gradio as gr
from .contracts import Assessment
from .presentation import feedback_html

log = logging.getLogger(__name__)


def local_time(value):
    return datetime.fromisoformat(value).astimezone(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M JST")


class Actions:
    def __init__(self, service):
        self.service = service

    def generate(self, words, level, progress=gr.Progress()):
        try:
            progress(.1, desc="Loading model / creating your exercise…")
            exercise = self.service.generate(words, level)
            return (exercise["id"], exercise["english"], "", "",
                    "Exercise ready. Translate the prompt using the target vocabulary.",
                    "、".join(json.loads(exercise["words"])))
        except Exception as exc:
            log.exception("Exercise generation failed")
            return gr.skip(), gr.skip(), gr.skip(), gr.skip(), f"Could not create an exercise: {exc}", gr.skip()

    def submit(self, exercise_id, answer, progress=gr.Progress()):
        if not exercise_id:
            return gr.skip(), "Create an exercise first."
        try:
            progress(.1, desc="Saving your answer / assessing Japanese…")
            result = self.service.assess(exercise_id, answer)
            return feedback_html(result), "Assessment saved. Retry this exercise or create a new one."
        except Exception as exc:
            log.exception("Assessment failed")
            return "", f"Could not assess your answer: {exc} Your answer remains in the box. Check History for saved submissions, then try again."

    def retry(self, exercise_id):
        if not exercise_id:
            return gr.skip(), gr.skip(), "Create an exercise first."
        return "", "", "Same exercise, fresh attempt. Earlier submissions remain in History."

    def refresh(self):
        rows = self.service.store.history()
        table, choices = [], []
        for row in rows:
            key = row["attempt_id"] or "exercise:" + row["exercise_id"]
            date = local_time(row["created_at"] or row["exercise_created_at"])
            score = Assessment.model_validate_json(row["feedback"]).overall if row["feedback"] else "—"
            status = row["status"] or "unanswered"
            vocabulary = "、".join(json.loads(row["words"]))
            if row["input_language"] != "ja":
                vocabulary = "Legacy English: " + vocabulary
            table.append([date, row["level"], vocabulary, row["english"], status, str(score)])
            choices.append((f'{date} · {row["level"]} · {status} · {row["english"][:65]} · {key[:8]}', key))
        return table, gr.Dropdown(choices=choices, value=None), ""

    def selected_row(self, key):
        for row in self.service.store.history():
            if key == (row["attempt_id"] or "exercise:" + row["exercise_id"]):
                return row
        raise ValueError("Select an exercise or attempt from History first.")

    def detail(self, key):
        if not key:
            return ""
        try:
            row = self.selected_row(key)
            content = f'<h3>English prompt</h3><p>{escape(row["english"])}</p>'
            label = "Japanese target vocabulary" if row["input_language"] == "ja" else "Original vocabulary (legacy English input)"
            content += f'<p><b>{label}:</b> {escape("、".join(json.loads(row["words"])))}</p>'
            if row["answer"] is not None:
                content += f'<h3>Your answer</h3><p class="japanese">{escape(row["answer"])}</p>'
            if row["feedback"]:
                content += feedback_html(Assessment.model_validate_json(row["feedback"]))
            elif row["error"]:
                content += f'<p>Assessment failed: {escape(row["error"])}</p>'
            else:
                content += "<p>No completed assessment yet.</p>"
            return content
        except ValueError as exc:
            return f"<p>{escape(str(exc))}</p>"

    def reopen(self, key):
        try:
            row = self.selected_row(key)
            words = "、".join(json.loads(row["words"])) if row["input_language"] == "ja" else ""
            status = ("Reopened for a new attempt. Practise: " + words + "." if words else
                      "Legacy exercise reopened for translation practice. Enter Japanese words when creating your next exercise.")
            return (row["exercise_id"], row["english"], "", "", status,
                    words, row["level"], gr.Tabs(selected="practice"),
                    words or "Legacy English input: " + ", ".join(json.loads(row["words"])))
        except ValueError as exc:
            return (*[gr.skip() for _ in range(4)], str(exc), gr.skip(), gr.skip(), gr.skip(), gr.skip())
