import logging
from dataclasses import dataclass

from diff_match_patch import diff_match_patch

logger = logging.getLogger("docdiff.utils")

dmp = diff_match_patch()


@dataclass
class TextDiff:
    diff_type: str  # "addition", "deletion", "modification", "equal"
    value_before: str
    value_after: str
    position: int


def compute_text_diff(text_before: str, text_after: str) -> list[TextDiff]:
    if text_before == text_after:
        return []
    diffs = dmp.diff_main(text_before, text_after)
    dmp.diff_cleanupSemantic(diffs)
    results: list[TextDiff] = []
    position = 0
    i = 0
    while i < len(diffs):
        op, text = diffs[i]
        if op == 0:
            position += len(text)
            i += 1
            continue
        if op == -1:
            if i + 1 < len(diffs) and diffs[i + 1][0] == 1:
                _, insert_text = diffs[i + 1]
                results.append(TextDiff(
                    diff_type="modification",
                    value_before=text,
                    value_after=insert_text,
                    position=position,
                ))
                position += len(text)
                i += 2
            else:
                results.append(TextDiff(
                    diff_type="deletion",
                    value_before=text,
                    value_after="",
                    position=position,
                ))
                position += len(text)
                i += 1
        elif op == 1:
            results.append(TextDiff(
                diff_type="addition",
                value_before="",
                value_after=text,
                position=position,
            ))
            i += 1
    return results


def compute_similarity(text_a: str, text_b: str) -> float:
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0
    diffs = dmp.diff_main(text_a, text_b)
    levenshtein = dmp.diff_levenshtein(diffs)
    max_len = max(len(text_a), len(text_b))
    return 1.0 - (levenshtein / max_len)
