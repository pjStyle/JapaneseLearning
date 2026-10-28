# Validation — 2026-10-28 (Japan time)

## Japanese vocabulary input update — version 8

The current app accepts **Japanese** study vocabulary. The initial English-input validation below is retained as a historical record.

- **30 software tests passed**, including Japanese input and Unicode normalization, generation meaning coverage, target-use output validation, independent scores, database migration, legacy history, and restoring the saved Japanese targets on reopen.
- **Five real-GPU generation checks passed** across N4/N3, nouns, verbs and adjectives. All prompts contained the chosen English meanings and satisfied the English length/sentence constraints. Repeated Japanese inputs produced different exercises. Records: `outputs/japanese_generation_results.json`.
- **Five focused real-model assessment checks passed**: conjugated `食べる` → `食べました`, kana `図書館` → `としょかん`, a valid synonym (`いただきました`) with full meaning credit but unused target feedback, adjective use, and an omitted target. Records: `outputs/vocabulary_check_results.json`.
- Japanese targets and their selected English meanings are saved with each new exercise. Existing English-input exercises remain labelled as legacy entries, retain their attempts, and can still be retried. Before the live migration, the database was backed up to `outputs/history_before_japanese_input.sqlite3`.
- The current exercise's target list is read-only and separate from the editable input for the next exercise. Target-use feedback accepts conjugation and kana, and does not change the three translation scores or their weights.

The updated interface and generation/assessment flow passed browser verification under the same offline guard described below. `雨、電車、傘` generated an English exercise about rain, an umbrella and a train; the submitted Japanese received feedback for all three targets. Editing the next input left the current targets unchanged. History retained the three earlier attempts and the new attempt, and reopening restored `雨、電車、傘` in both the input and current-target list. Preview: `outputs/japanese-vocabulary-preview.jpg`.

## Environment

Windows, NVIDIA RTX 5070 Ti (16,303 MiB), driver 610.88, Python 3.12.14, CUDA PyTorch 2.11.0+cu128. All 66 installed packages passed `uv pip check`; exact versions are in `requirements.lock.txt`.

Model: official Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, text-only `Qwen3_5ForCausalLM`, NF4 double quantization with BF16 compute, thinking disabled, greedy decoding. CUDA kernels for NF4 were checked before full-model loading. Optional causal-convolution/linear-attention kernels are absent; Transformers uses its reference PyTorch paths.

## Software checks

`python -m pytest -q`: **23 passed**. Covers input and output validation, weighted scoring, independent source-free reading, correction filtering, safe rendering, answer persistence before inference, failure recovery, startup interruption recovery, separate/concurrent attempts, history reopening, unavailable GPU, missing checkpoints, download failures and malformed-output repair.

PowerShell setup and launch scripts passed parser checks. Initial installation completed in a separate project-local environment. The official checkpoint downloaded completely; abandoned temporary shards from download investigation were removed after completion.

## Assessment investigation

The first single-pass rubric incorrectly gave full credit to a giver/recipient reversal. Calibration improved independent grammar scores but did not resolve that reversal. A focused 8-bit comparison also missed it and used about 10.5 GiB of allocated GPU memory; its requests took roughly 15–24 seconds. It was not adopted.

The final 4-bit flow first translates the learner answer into English without seeing the source, then assesses source fidelity and Japanese quality. This resolved the tested reversal. The inferred English reading is visible in feedback. The application derives its headline from validated scores, removes no-op corrections, and suppresses optional style rewrites when meaning needs work.

Final fixed assessment evaluation, prompt version **6**: **22 cases, zero automated gate failures**. All ten valid alternatives received full scores, including kana and plain/polite variants. Meaning-changing errors scored below valid alternatives; the incorrect-particle case had lower grammar credit. English-only instruction text received zero scores, and embedded grading instructions did not override the source. Version **7** changes only exercise generation; assessment prompts and deterministic decoding are unchanged.

An N4 browser request initially remained below the minimum length after repair. Version 7 adds a two-sentence size example and uses sampling for generation, while interpretation and assessment remain greedy. Five subsequent real-GPU generation checks passed all word-count, sentence-count and supplied-word constraints, covering N4/N3 and one, two and three input words. Two requests for `coffee, book` produced different valid exercises. Warm generation took 1.1–1.9 seconds in that check. Records: `outputs/generation_results.json`.

Complete local records:

- `outputs/evaluation/results.json`: final scores, feedback, examples, English readings and timings, with application headline handling applied.
- `outputs/evaluation/model_v6_results.json`: model-run results before the final headline policy.
- `outputs/evaluation/gates.json`: automated checks.
- `outputs/evaluation/baseline_v*_results.json`, `outputs/precision8_results.json`, `outputs/meaning_probe.json`: retained investigation records.

The implementation agent inspected every final correction and example. This is a development set used to tune prompts, not a held-out benchmark or certified grading test. Some teaching wording and example naturalness remain imperfect: giving-verb perspective and romanized terminology produced awkward or inaccurate wording. Feedback is provisional study assistance; independent Japanese-speaker review is recommended. The source-free reading and visible comparison help expose misinterpretations but cannot eliminate model errors.

## Performance

Full-model cold loading measured about **9 seconds** after Python imports. Warm generation of the tested 20-word exercise took **1.5 seconds**. Across the final evaluation's 21 warm assessments, including independent reading and any repair, latency was **3.7–14.5 seconds**, median **7.2 seconds**. Peak PyTorch allocated GPU memory was **7.44 GiB**. These measurements met the 30-second warm-operation target on this machine.

PyTorch allocated memory excludes Windows/display use, driver overhead and reserved memory. First-process startup also includes Python/library imports. Timings are recorded in `outputs/timings.jsonl`; these small samples do not establish performance for every answer.

## Browser and offline checks

The normal browser flow passed: N3 default, real GPU generation and assessment, scores and Japanese example, retry clearing answer/feedback while retaining the prompt, two separate saved attempts, feedback review in History, and reopening an exercise for a fresh attempt. After a process restart, both attempts and their feedback remained available, and reopening worked.

Offline verification passed through `scripts.offline_app`, which denies external Python DNS/TCP access while allowing localhost. It does not disable the machine's network adapters or install firewall rules. The guarded browser flow loaded and reopened saved history, generated a fresh N4 exercise (`coffee, book`), assessed its Japanese translation, and saved the completed attempt. Generation repaired one invalid first response, then succeeded in about 2.6 seconds of inference; independent reading plus assessment took about 6.1 seconds. Peak allocated GPU memory in this final browser test was 7.45 GiB. The app remains running on `http://127.0.0.1:7861`.

Screenshots: `outputs/app-preview.jpg` (normal N3 practice flow) and `outputs/offline-preview.jpg` (final guarded N4 practice flow). The local practice database contains two N3 test attempts and one N4 test attempt for inspection. Unit tests and model evaluation use separate temporary/development databases.
