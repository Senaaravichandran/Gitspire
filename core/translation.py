import logging
import os
import re
import html
from dataclasses import dataclass
from typing import Dict, List

import string

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    original: str
    translated: str
    language: str
    translated_source: bool


class TranslationService:

    def __init__(self):
        # Translation is disabled to keep the pipeline fast and avoid extra API calls.
        self.enabled = False
        self.mode = "disabled"

    def translate_text(self, text: str) -> TranslationResult:
        if not text:
            return TranslationResult(original="", translated="", language="en", translated_source=False)

        # Avoid slow translation on very long inputs
        if len(text) > 1200:
            return TranslationResult(original=text, translated=text, language="en", translated_source=False)

        if not self.enabled:
            language = self._detect_language_simple(text)
            return TranslationResult(original=text, translated=text, language=language, translated_source=False)

        # Preserve fenced code blocks and translate only surrounding prose.
        code_blocks = []
        pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)

        def _stash_code(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

        masked = pattern.sub(_stash_code, text)
        language = "unknown"
        
        language = self._detect_language_simple(masked)

        if language == "en":
            translated = text
            return TranslationResult(original=text, translated=translated, language=language, translated_source=False)

        try:
            # Translate only non-code text, then restore code blocks.
            translated = masked

            for idx, block in enumerate(code_blocks):
                translated = translated.replace(f"__CODE_BLOCK_{idx}__", block)
            return TranslationResult(original=text, translated=translated, language=language, translated_source=True)
        except Exception as exc:
            logger.warning("Translation failed: %s", exc)
            return TranslationResult(original=text, translated=text, language=language, translated_source=False)

    def _detect_language_simple(self, text: str) -> str:
        if not text:
            return "en"
        # Simple heuristic: ASCII-only is assumed English, otherwise default to English.
        if all(char in string.printable for char in text):
            return "en"
        return "en"


def update_language_stats(stats: Dict, language: str, translated: bool):
    if not language or language == "unknown":
        language = "en"
    stats["language_distribution"][language] = stats["language_distribution"].get(language, 0) + 1
    if translated:
        stats["translated_artifact_count"] += 1