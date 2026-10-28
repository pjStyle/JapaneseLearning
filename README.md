# Japanese practice

A personal, local Windows app for short English-to-Japanese translation practice at approximately JLPT N4/N3. N3 is the default. Enter 1–3 **Japanese words you want to practise**, such as `雨、電車、傘`, translate a short generated English prompt, and receive English coaching and a Japanese example.

## Install and run

Requirements: Windows, an NVIDIA CUDA GPU (target RTX 5070 Ti, 16 GB), [uv](https://docs.astral.sh/uv/getting-started/installation/), and internet for setup. Allow roughly 30 GB for the environment and model, plus temporary package-download cache space.

```powershell
.\setup.cmd
.\launch.cmd
```

Setup installs project-local Python 3.12, CUDA PyTorch and pinned dependencies, then downloads the official [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) checkpoint, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Its weights total 19,306,216,416 bytes (about 18 GiB). It is Apache 2.0 licensed. Setup can be rerun after download failures; completed files are reused, but an interrupted shard may need to download again.

Launch opens `http://127.0.0.1:7861`. No account or public sharing is enabled. Runtime uses local model files only, with Hub offline mode and telemetry disabled. The first request loads the model; later requests reuse it. One GPU request runs at a time. Close the launcher window or press Ctrl+C there to stop.

The scripts change PowerShell execution policy only for their own process. They do not modify the image-generation project's environment or model files.

## Practice and feedback

The Practice tab accepts kanji, hiragana and katakana, with `、`, commas or newlines as separators. It creates 1–2 English sentences, around 15–35 words, using an everyday meaning of each Japanese target. For example, `傘` makes the prompt include “umbrella,” so you can practise producing `傘` in context. Japanese examples appear only after assessment. Difficulty is an approximate practice target, not a JLPT certification.

Meaning, grammar and naturalness each receive a 0–10 score. The app calculates the overall score as `0.5 × meaning + 0.3 × grammar + 0.2 × naturalness`, rounded to one decimal. Coaching separates errors from optional improvements, accepts kana and consistent plain or polite forms, and offers one possible Japanese translation.

Assessment first reads your Japanese without seeing the English exercise, then compares that reading with the source. The feedback shows this English reading so you can spot a mistaken interpretation. Grammar and naturalness are assessed separately from meaning. No-op corrections are removed, and optional style suggestions wait until meaning is substantially correct.

**Target vocabulary** feedback checks each chosen Japanese word separately. Appropriate conjugations (`食べる` → `食べました`) and kana spellings count. A valid synonym can earn full translation credit while the original target is marked unused, encouraging focused practice without changing the score weights.

Retry clears the answer and feedback while retaining the exercise. New exercise generates another prompt using the current words and level. The History tab shows previous attempts, including failures, and can reopen an exercise for another attempt. Each submission is independent; rapid repeated submissions create separate saved attempts.

History created with the earlier English-input version remains readable and retryable, labelled “Legacy English.” Those entries do not populate the Japanese input when reopened. New exercises save both the Japanese targets and the English meanings used to generate the prompt.

Model feedback is provisional study assistance. Valid alternatives should be accepted, but a local model can still make mistakes. Development evaluation results and measured performance belong in [VALIDATION.md](VALIDATION.md).

## Local data and troubleshooting

- `models/Qwen3.5-9B/`: pinned model files; required for offline use.
- `data/practice.sqlite3`: exercises, answers, feedback, timestamps, and model/prompt provenance. Back up this file while the app is stopped to retain your history.
- `outputs/timings.jsonl`: load and inference latency and PyTorch peak allocated GPU memory. It does not contain your answers.
- `outputs/evaluation/`: development assessment results, separate from your practice history.

Submitted answers are committed before inference. If assessment fails, the answer remains visible and is saved in History without a score. Submit again to create another attempt. Malformed model output gets one repair attempt, then a visible error. Restarting marks interrupted pending attempts as failed.

For missing or incomplete model files, rerun `setup.cmd` online. For CUDA errors, check the NVIDIA driver and close other GPU-heavy applications. This app does not coordinate GPU memory with the Qwen image app. No CPU inference fallback is provided.

## Development checks

Stop the app before running GPU smoke or evaluation scripts so only one model occupies the GPU.

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m scripts.smoke_model
.venv\Scripts\python.exe -m scripts.evaluate
.venv\Scripts\python.exe -m scripts.check_generation
.venv\Scripts\python.exe -m scripts.check_vocabulary
```

For offline verification, stop the normal app and run `.venv\Scripts\python.exe -m scripts.offline_app`. This test harness blocks external Python DNS/TCP access while allowing localhost; it does not change Windows network settings.

The fixed evaluation contains 22 examples with valid alternatives, kana, register, particles, tense, negation, omissions, unrelated text and instruction-like submissions. It saves complete feedback and checks valid-versus-invalid meaning scores. Human review remains necessary; this is not a certified grading benchmark.
