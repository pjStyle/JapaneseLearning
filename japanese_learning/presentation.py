"""Escape model/learner text before displaying it in HTML."""
from html import escape
from .contracts import Assessment


def coaching_summary(result: Assessment) -> str:
    """Keep the headline grounded in validated scores; details come from corrections."""
    if result.meaning == result.grammar == result.naturalness == 0:
        return "Try writing a Japanese translation of the English prompt."
    notes = []
    if result.meaning >= 9:
        notes.append("Your translation preserves the English meaning.")
    else:
        notes.append("Check that your answer preserves all the English meaning.")
    if result.grammar < 9:
        notes.append("Review the grammar corrections and the Japanese example.")
    if result.naturalness < 9:
        notes.append("Compare the phrasing with the Japanese example.")
    if result.grammar >= 9 and result.naturalness >= 9:
        notes.append("Your Japanese reads well.")
    return " ".join(notes)


def feedback_html(result: Assessment) -> str:
    scores = [("Overall", result.overall), ("Meaning", result.meaning),
              ("Grammar", result.grammar), ("Naturalness", result.naturalness)]
    cards = "".join(f'<div class="score"><strong>{score:g}<small>/10</small></strong><span>{label}</span></div>'
                    for label, score in scores)
    corrections = "".join(
        f'<li><b>{"Error" if item.kind == "error" else "Optional improvement"}</b>'
        f'<p>{escape(item.original)} → {escape(item.suggested)}</p><p>{escape(item.explanation)}</p></li>'
        for item in result.corrections)
    vocabulary = "".join(f'<li><b>{escape(item.word)}</b> — {"Used" if item.used else "Not used"}: {escape(item.note)}</li>'
                         for item in result.vocabulary_usage)
    return (f'<div class="feedback"><div class="scores">{cards}</div><p>{escape(result.summary)}</p>'
            + (f'<p><b>Your answer was read as:</b> {escape(result.interpreted_english)}</p>' if result.interpreted_english else "")
            + (f'<h3>Target vocabulary</h3><ul>{vocabulary}</ul>' if vocabulary else "")
            + (f'<ol>{corrections}</ol>' if corrections else "")
            + f'<h3>One possible Japanese translation</h3><p class="japanese">{escape(result.japanese_example)}</p></div>')
