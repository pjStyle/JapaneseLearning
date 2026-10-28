import os

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import gradio as gr
from filelock import FileLock, Timeout
from japanese_learning.config import ROOT
from japanese_learning.inference import LocalModel
from japanese_learning.service import PracticeService
from japanese_learning.storage import Store
from japanese_learning.ui_actions import Actions

CSS = """
.gradio-container {max-width: 1050px !important; margin: auto !important;}
.hero {padding: 18px 0 14px;}
.hero .eyebrow {font-size: 12px; letter-spacing: .16em; color: #688d80; font-weight: 700;}
.hero h1 {font-size: 32px; margin: 5px 0 8px; font-weight: 650; letter-spacing: -.03em;}
.hero p {color: var(--body-text-color-subdued); font-size: 15px;}
.scores {display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 18px;}
.score {border: 1px solid var(--border-color-primary); border-radius: 12px; padding: 16px 12px; background: var(--background-fill-secondary);}
.score strong {display: block; font-size: 27px; line-height: 1.2;}
.score small {font-size: 13px; font-weight: normal; opacity: .65; margin-left: 3px;}
.score span {font-size: 12px; color: var(--body-text-color-subdued);}
.feedback {line-height: 1.7; padding: 12px 0; overflow-wrap: anywhere;}
.feedback p {white-space: pre-wrap; margin: 8px 0 14px;}
.feedback ol {padding-left: 24px;}
.feedback h3 {font-weight: 650; margin-top: 16px;}
.japanese {font-size: 19px; line-height: 1.9; white-space: pre-wrap;}
@media(max-width: 500px) {.scores {grid-template-columns: repeat(2,1fr);} .hero h1 {font-size: 27px;}}
"""


def build_app(service=None):
    actions = Actions(service or PracticeService(LocalModel(), Store()))
    with gr.Blocks(title="Japanese practice", analytics_enabled=False) as demo:
        gr.HTML('<div class="hero"><div class="eyebrow">日々の日本語 · DAILY PRACTICE</div>'
                '<h1>A little Japanese, every day.</h1>'
                '<p>Choose a few words. Translate a small moment. Learn from your next attempt.</p></div>')
        exercise_id = gr.State(None)
        with gr.Tabs(selected="practice") as tabs:
            with gr.Tab("Practice", id="practice"):
                with gr.Row():
                    words = gr.Textbox(label="Japanese words to practise", placeholder="雨、電車、傘",
                                       info="1–3 Japanese words, separated by 、 or commas. Kanji and kana are welcome.", scale=4)
                    level = gr.Dropdown(["N4", "N3"], value="N3", label="Approximate level", scale=1)
                new = gr.Button("New exercise", variant="primary")
                prompt = gr.Textbox(label="Translate this into Japanese", interactive=False, lines=3,
                                    placeholder="Your English exercise will appear here.")
                exercise_targets = gr.Textbox(label="Targets for this exercise", interactive=False,
                                               placeholder="Your chosen Japanese words will appear here.")
                gr.Markdown("Use your chosen Japanese vocabulary in your translation. Conjugations and kana spellings count.")
                answer = gr.Textbox(label="Your Japanese translation", lines=4, max_lines=10,
                                    placeholder="ここに日本語で書いてください。")
                with gr.Row():
                    submit = gr.Button("Assess my Japanese", variant="primary")
                    retry = gr.Button("Retry this exercise")
                status = gr.Textbox(label="Status", value="Create an exercise to begin. The model loads on your first request.",
                                    interactive=False, lines=2)
                feedback = gr.HTML()
                gr.Markdown("Meaning **50%** · Grammar **30%** · Naturalness **20%**. "
                            "Feedback is a study aid; valid translations can differ from the example.")
            with gr.Tab("History", id="history") as history_tab:
                gr.Markdown("Your exercises and attempts are saved on this computer. Times are shown in Japan time.")
                refresh = gr.Button("Refresh history")
                history = gr.Dataframe(headers=["Date", "Level", "Vocabulary", "English prompt", "Status", "Overall / 10"],
                                       datatype="str", type="array", interactive=False, wrap=True, max_height=350)
                selection = gr.Dropdown(label="Exercise or attempt", choices=[], interactive=True,
                                        info="Select an entry to view its answer and feedback.")
                reopen = gr.Button("Reopen for a new attempt", variant="primary")
                detail = gr.HTML()
        shared = dict(concurrency_id="practice", concurrency_limit=1)
        new.click(actions.generate, [words, level], [exercise_id, prompt, answer, feedback, status, exercise_targets],
                  api_name="new_exercise", **shared)
        submit.click(actions.submit, [exercise_id, answer], [feedback, status], api_name="assess", **shared)
        retry.click(actions.retry, [exercise_id], [answer, feedback, status], api_name="retry", **shared)
        for event in (refresh.click, history_tab.select, demo.load):
            event(actions.refresh, outputs=[history, selection, detail], api_name=False, **shared)
        selection.change(actions.detail, [selection], [detail], api_name=False, **shared)
        reopen.click(actions.reopen, [selection], [exercise_id, prompt, answer, feedback, status, words, level, tabs, exercise_targets],
                     api_name="reopen", **shared)
    return demo.queue(default_concurrency_limit=1)


def main():
    (ROOT / "data").mkdir(exist_ok=True)
    try:
        with FileLock(ROOT / "data" / "app.lock", timeout=0):
            build_app().launch(server_name="127.0.0.1", server_port=7861, share=False,
                               inbrowser=os.environ.get("JP_NO_BROWSER") != "1", show_error=False,
                               theme=gr.themes.Soft(primary_hue="emerald", neutral_hue="slate",
                                                    font=["Segoe UI", "Yu Gothic", "sans-serif"],
                                                    font_mono=["Consolas", "monospace"]),
                               css=CSS, footer_links=[], enable_monitoring=False)
    except Timeout:
        raise SystemExit("Japanese practice is already running. Open http://127.0.0.1:7861.")


if __name__ == "__main__":
    main()
