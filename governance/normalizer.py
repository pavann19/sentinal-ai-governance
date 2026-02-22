# core/normalizer.py
# Prompt normalization layer for obfuscation-resistant symbolic detection.
# Applied BEFORE symbolic rule matching. Does NOT affect embeddings.

import re
import unicodedata


# Cyrillic -> Latin homoglyph mapping
HOMOGLYPH_MAP = {
    "\u043e": "o",  # о -> o
    "\u0430": "a",  # а -> a
    "\u0435": "e",  # е -> e
    "\u0440": "p",  # р -> p
    "\u0441": "c",  # с -> c
    "\u0445": "x",  # х -> x
    "\u04e9": "o",  # ө -> o
    "\u0456": "i",  # і -> i
}

# Zero-width and invisible characters to strip
ZERO_WIDTH_CHARS = re.compile(
    "[\u200b\u200c\u200d\u200e\u200f"   # zero-width space/joiner/non-joiner/marks
    "\u2060\u2061\u2062\u2063"           # word joiner, invisible operators
    "\ufeff"                             # BOM / zero-width no-break space
    "\u00ad"                             # soft hyphen
    "]"
)

# Pattern: single characters separated by spaces (e.g. "b o m b")
SPACED_CHARS_PATTERN = re.compile(r"\b([a-z])\s(?=[a-z]\b)")


def normalize_prompt(prompt: str) -> str:
    """
    Normalizes a prompt for robust symbolic detection.

    Steps:
        1) Unicode NFKC normalization
        2) Lowercase
        3) Remove zero-width / invisible characters
        4) Replace Cyrillic homoglyphs with Latin equivalents
        5) Collapse multiple whitespace into single space
        6) Collapse single-character spacing patterns (e.g. "b o m b" -> "bomb")
        7) Strip leading/trailing whitespace

    Does NOT alter semantic meaning for embedding purposes.
    This function should ONLY be used for symbolic rule matching.
    """
    # 1) Unicode NFKC normalization (canonical decomposition + compatibility composition)
    text = unicodedata.normalize("NFKC", prompt)

    # 2) Lowercase
    text = text.lower()

    # 3) Remove zero-width and invisible characters
    text = ZERO_WIDTH_CHARS.sub("", text)

    # 4) Replace Cyrillic homoglyphs
    for cyrillic, latin in HOMOGLYPH_MAP.items():
        text = text.replace(cyrillic, latin)

    # 5) Collapse multiple whitespace (spaces, tabs, special unicode spaces) into one
    text = re.sub(r"\s+", " ", text)

    # 6) Collapse spaced single characters: "b o m b" -> "bomb"
    #    Apply repeatedly until no more matches
    prev = None
    while prev != text:
        prev = text
        text = SPACED_CHARS_PATTERN.sub(r"\1", text)

    # 7) Strip
    text = text.strip()

    return text
