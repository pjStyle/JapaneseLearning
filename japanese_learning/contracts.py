import json
import math
import re
import unicodedata
from pydantic import BaseModel, ConfigDict, Field, field_validator


def parse_words(raw: str) -> list[str]:
    raw = unicodedata.normalize("NFKC", raw)
    words = [w.strip() for w in re.split(r"[,、\n]", raw) if w.strip()]
    if not 1 <= len(words) <= 3 or len(set(words)) != len(words):
        raise ValueError("Enter 1–3 different Japanese words, separated by commas or 、.")
    if any(not re.fullmatch(r"[\u3041-\u3096\u30a1-\u30fa\u30fc\u30fb\u3400-\u9fff々〆ヶ]+", w) or len(w) > 40 for w in words):
        raise ValueError("Use Japanese vocabulary in kanji, hiragana or katakana, for example 雨、電車、傘.")
    return words


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class VocabularyMeaning(StrictModel):
    word: str = Field(min_length=1, max_length=40)
    english: str = Field(min_length=1, max_length=80)

    @field_validator("english")
    @classmethod
    def english_gloss(cls, value):
        if not re.fullmatch(r"[A-Za-z]+(?:[-' ][A-Za-z]+)*", value) or len(value.split()) > 5:
            raise ValueError("Use a short English word or phrase as the vocabulary meaning.")
        return value


class ExerciseResult(StrictModel):
    english: str = Field(min_length=1, max_length=500)
    targets: list[VocabularyMeaning] = Field(default_factory=list, max_length=3)

    def check(self, words: list[str]):
        tokens = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", self.english)
        sentences = [s for s in re.split(r"[.!?]+", self.english) if s.strip()]
        if not 15 <= len(tokens) <= 35 or not 1 <= len(sentences) <= 2:
            raise ValueError(f"The prompt has {len(tokens)} words and {len(sentences)} sentences. Rewrite it as 1–2 sentences with about 25 English words (required range 15–35).")
        if re.search(r"[^\x00-\x7f]", self.english):
            raise ValueError("The exercise must contain English text only.")
        if [target.word for target in self.targets] != words:
            raise ValueError("Return targets for every supplied Japanese word, in the same order, with no additions.")
        for target in self.targets:
            if not re.search(r"(?<![A-Za-z])" + re.escape(target.english) + r"(?![A-Za-z])", self.english, re.I):
                raise ValueError(f"The English prompt must include the chosen meaning '{target.english}' for '{target.word}'.")
        return self


class Interpretation(StrictModel):
    english: str = Field(min_length=1, max_length=2000)


class Correction(StrictModel):
    kind: str
    original: str = Field(max_length=500)
    suggested: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=1000)

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, value):
        if value not in ("error", "improvement"):
            raise ValueError("kind must be error or improvement")
        return value


class VocabularyUsage(StrictModel):
    word: str = Field(min_length=1, max_length=40)
    used: bool
    note: str = Field(min_length=1, max_length=500)


class Assessment(StrictModel):
    meaning: float = Field(ge=0, le=10)
    grammar: float = Field(ge=0, le=10)
    naturalness: float = Field(ge=0, le=10)
    summary: str = Field(min_length=1, max_length=1500)
    corrections: list[Correction] = Field(max_length=3)
    japanese_example: str = Field(min_length=1, max_length=1000)
    interpreted_english: str = Field(default="", max_length=2000)
    vocabulary_usage: list[VocabularyUsage] = Field(default_factory=list, max_length=3)

    def check_targets(self, targets):
        if [item.word for item in self.vocabulary_usage] != [item["word"] for item in targets]:
            raise ValueError("Return one vocabulary_usage entry for each target word, in the supplied order.")
        return self

    @field_validator("meaning", "grammar", "naturalness", mode="before")
    @classmethod
    def numeric_score(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Scores must be finite numbers.")
        return float(value)

    @field_validator("japanese_example")
    @classmethod
    def japanese_required(cls, value):
        if not re.search(r"[\u3040-\u30ff\u3400-\u9fff]", value):
            raise ValueError("The example must contain Japanese.")
        return value

    @property
    def overall(self) -> float:
        return round(self.meaning * .5 + self.grammar * .3 + self.naturalness * .2, 1)


def decode_result(text: str, model):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return model.model_validate(json.loads(text))
