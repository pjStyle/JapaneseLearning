import threading
import json
from .contracts import Assessment, ExerciseResult, Interpretation, decode_result, parse_words
from .prompts import ASSESSOR, GENERATOR, INTERPRETER, VOCABULARY_ASSESSMENT, assessment_data, generation_data
from .presentation import coaching_summary


class PracticeService:
    def __init__(self, model, store):
        self.model, self.store = model, store
        self.lock = threading.RLock()

    def structured(self, system, data, result_type, operation, check=None):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": data}]
        for index in range(2):
            raw = self.model.complete(messages, operation=operation)
            try:
                result = decode_result(raw, result_type)
                return check(result) if check else result
            except (ValueError, TypeError) as exc:
                if index:
                    raise RuntimeError("The model returned invalid output twice. Please try again.") from exc
                messages += [{"role": "assistant", "content": raw},
                             {"role": "user", "content": "Repair the output to satisfy the original JSON format and constraints. Validation error: " + str(exc)[:1000]}]

    def generate(self, raw_words, level):
        words = parse_words(raw_words)
        if level not in ("N4", "N3"):
            raise ValueError("Choose N4 or N3.")
        with self.lock:
            result = self.structured(GENERATOR, generation_data(words, level), ExerciseResult,
                                     "generate", lambda value: value.check(words))
            return self.store.create_exercise(words, level, result.english,
                                               targets=[target.model_dump() for target in result.targets])

    def assess(self, exercise_id, answer):
        if not answer or not answer.strip():
            raise ValueError("Write your Japanese translation first.")
        if len(answer) > 2000:
            raise ValueError("Please keep your answer under 2,000 characters.")
        with self.lock:
            exercise = self.store.exercise(exercise_id)
            attempt_id = self.store.start_attempt(exercise_id, answer)
            try:
                result = self.evaluate_answer(exercise["english"], answer, exercise["level"],
                                              json.loads(exercise["targets"]))
                self.store.finish(attempt_id, feedback=result)
                return result
            except Exception as exc:
                self.store.finish(attempt_id, error=str(exc))
                raise

    def evaluate_answer(self, english, answer, level, targets=None):
        reading = self.structured(INTERPRETER, json.dumps({"japanese": answer}, ensure_ascii=False),
                                  Interpretation, "interpret")
        targets = targets or []
        result = self.structured(ASSESSOR + (VOCABULARY_ASSESSMENT if targets else ""),
                                 assessment_data(english, answer, level, reading.english, targets),
                                 Assessment, "assess", lambda value: value.check_targets(targets))
        # Focus feedback on substantive errors before optional stylistic rewrites.
        corrections = [item for item in result.corrections if item.original.strip() != item.suggested.strip()
                       and (item.kind == "error" or (result.meaning >= 9 and result.naturalness < 10))]
        return result.model_copy(update={"interpreted_english": reading.english, "corrections": corrections,
                                         "summary": coaching_summary(result)})
