import logging
import re
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
    """Compute word-level text diff using diff-match-patch.

    Uses word-level granularity to avoid character fragmentation.
    E.g., "18%" → "21%" produces ONE modification, not two character ops.
    """
    if text_before == text_after:
        return []

    # Word-level diff: map words to chars, diff chars, map back
    words_a, words_b, char_array = _words_to_chars(text_before, text_after)
    diffs = dmp.diff_main(words_a, words_b, False)
    dmp.diff_cleanupSemantic(diffs)
    _chars_to_words(diffs, char_array)

    # Now each diff entry is at word-level granularity
    results: list[TextDiff] = []
    position = 0
    i = 0
    while i < len(diffs):
        op, text = diffs[i]
        if op == 0:  # EQUAL
            position += len(text)
            i += 1
            continue
        if op == -1:  # DELETE
            if i + 1 < len(diffs) and diffs[i + 1][0] == 1:
                # Modification (delete + insert pair)
                _, insert_text = diffs[i + 1]
                results.append(TextDiff(
                    diff_type="modification",
                    value_before=text.strip(),
                    value_after=insert_text.strip(),
                    position=position,
                ))
                position += len(text)
                i += 2
            else:
                results.append(TextDiff(
                    diff_type="deletion",
                    value_before=text.strip(),
                    value_after="",
                    position=position,
                ))
                position += len(text)
                i += 1
        elif op == 1:  # INSERT
            results.append(TextDiff(
                diff_type="addition",
                value_before="",
                value_after=text.strip(),
                position=position,
            ))
            i += 1

    # Filter out empty diffs
    return [r for r in results if r.value_before or r.value_after]


def _words_to_chars(text1: str, text2: str) -> tuple[str, str, list[str]]:
    """Map words to single characters for word-level diffing.

    Similar to diff_match_patch.diff_linesToChars_ but operates on words.
    """
    word_array: list[str] = [""]  # Index 0 is unused
    word_hash: dict[str, str] = {}

    def _map_words(text: str) -> str:
        chars = []
        # Split on word boundaries, keeping whitespace
        tokens = re.findall(r'\S+|\s+', text)
        for token in tokens:
            if token in word_hash:
                chars.append(word_hash[token])
            else:
                word_array.append(token)
                char = chr(len(word_array) - 1)
                word_hash[token] = char
                chars.append(char)
        return "".join(chars)

    chars1 = _map_words(text1)
    chars2 = _map_words(text2)
    return chars1, chars2, word_array


def _chars_to_words(diffs: list, word_array: list[str]) -> None:
    """Convert character-based diffs back to word-based diffs in-place."""
    for i in range(len(diffs)):
        text = []
        for char in diffs[i][1]:
            text.append(word_array[ord(char)])
        diffs[i] = (diffs[i][0], "".join(text))


def compute_similarity(text_a: str, text_b: str) -> float:
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0
    diffs = dmp.diff_main(text_a, text_b)
    levenshtein = dmp.diff_levenshtein(diffs)
    max_len = max(len(text_a), len(text_b))
    return 1.0 - (levenshtein / max_len)


# ---------------------------------------------------------------------------
# OCR garbage detection helpers
# ---------------------------------------------------------------------------

_RE_NON_LATIN_CLUSTER = re.compile(r"[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF]{3,}")
_RE_GARBLED = re.compile(r"[^\w\s.,;:!?()'\"-]{3,}")
_RE_PAGE_NUMBER = re.compile(r"^\s*(?:page\s+)?\d+\s*(?:of\s+\d+)?\s*$", re.IGNORECASE)
_RE_HEADER_FOOTER_PATTERN = re.compile(
    r"(?:rev\.?\s*\d|page\s+\d|^\d+\s+of\s+\d+$|confidential|draft|proprietary)",
    re.IGNORECASE,
)


def is_ocr_garbage(text: str) -> bool:
    """Detect if text is likely OCR garbage (garbled characters, non-Latin clusters)."""
    if not text or len(text.strip()) < 2:
        return False
    stripped = text.strip()
    # Non-Latin character clusters (Hindi, symbol fonts, etc.)
    if _RE_NON_LATIN_CLUSTER.search(stripped):
        return True
    # High ratio of non-alphanumeric characters
    alnum = sum(1 for c in stripped if c.isalnum() or c.isspace())
    if len(stripped) > 5 and alnum / len(stripped) < 0.4:
        return True
    # Contains garbled sequences
    if _RE_GARBLED.search(stripped):
        return True
    return False


def is_page_number_text(text: str) -> bool:
    """Detect if text matches a page number pattern like 'Page 5 of 12'."""
    return bool(_RE_PAGE_NUMBER.match(text.strip()))


def is_header_footer_text(text: str) -> bool:
    """Detect if text looks like a recurring header/footer element."""
    stripped = text.strip()
    if len(stripped) > 200:
        return False  # Too long for header/footer
    return bool(_RE_HEADER_FOOTER_PATTERN.search(stripped))
