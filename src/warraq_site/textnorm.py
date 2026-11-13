"""Arabic search folding, shared by the index builder and (mirrored) by assets/js/search.js.

The rules match arabic-bib's search fold so that a query typed on the site and a name typed in the
library agree: tashkeel and tatweel dropped, alef forms to bare alef, ة→ه, ى→ي, ؤ→و, ئ→ي, ء dropped,
presentation forms through NFKC, Persian ی/ک to Arabic, Arabic-Indic and Persian digits to ASCII,
punctuation to space, Latin casefolded.
"""

from __future__ import annotations

import re
import unicodedata

_TASHKEEL = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ء": None,
        "ی": "ي",
        "ک": "ك",
        **{chr(0x0660 + i): str(i) for i in range(10)},
        **{chr(0x06F0 + i): str(i) for i in range(10)},
    }
)
_PRESENTATION = re.compile("[ﭐ-﷿ﹰ-﻿]+")
_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)

# Clitic prefixes stripped for matching («والكتب» finds «كتب»); only when enough of the word remains.
PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك")


def fold(text: str) -> str:
    """Fold text for search: the same output for every spelling variant of a word."""
    text = _PRESENTATION.sub(lambda m: unicodedata.normalize("NFKC", m.group()), text)
    text = _TASHKEEL.sub("", text)
    text = text.translate(_MAP).casefold()
    text = text.replace("_", " ")
    return " ".join(_NON_WORD.sub(" ", text).split())


def stem(word: str) -> str:
    """Strip one clitic prefix when at least three letters remain."""
    for p in PREFIXES:
        if word.startswith(p) and len(word) - len(p) >= 3:
            return word[len(p) :]
    return word


def tokens(text: str) -> list[str]:
    return [stem(w) for w in fold(text).split()]
