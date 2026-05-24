import logging
import os
import re
import html
from dataclasses import dataclass
from typing import Dict, List

import httpx

try:
    from google.cloud import translate_v2 as translate
except Exception:  # pragma: no cover - optional dependency at runtime
    translate = None

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    original: str
    translated: str
    language: str
    translated_source: bool


class TranslationService:

    def __init__(self):
        enabled_env = os.environ.get("TRANSLATION_ENABLED", "true").strip().lower()
        self.enabled = enabled_env in {"1", "true", "yes", "y"}
        self.mode = "disabled"
        self.api_key = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "").strip()
        self.rest_client = None

        if not self.enabled:
            self.client = None
            return

        if self.api_key:
            self.mode = "api_key"
            self.client = None
            self.rest_client = httpx.Client(timeout=15.0)
            return

        if translate is None:
            logger.warning("google-cloud-translate not available; disabling translation")
            self.enabled = False
            self.client = None
            return

        try:
            self.client = translate.Client()
            self.mode = "library"
        except Exception as exc:
            logger.warning("Translation client init failed: %s", exc)
            self.enabled = False
            self.client = None

    def translate_text(self, text: str) -> TranslationResult:
        if not text:
            return TranslationResult(original="", translated="", language="unknown", translated_source=False)

        if not self.enabled or (self.client is None and not self.api_key):
            return TranslationResult(original=text, translated=text, language="unknown", translated_source=False)

        # Preserve fenced code blocks and translate only surrounding prose.
        code_blocks = []
        pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)

        def _stash_code(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

        masked = pattern.sub(_stash_code, text)
        language = "unknown"
        if self.mode == "api_key":
            language = self._detect_language_api(masked)
        else:
            try:
                detected = self.client.detect_language(masked)
                language = detected.get("language", "unknown") if isinstance(detected, dict) else "unknown"
            except Exception as exc:
                logger.warning("Language detection failed: %s", exc)
                language = "unknown"

        if language == "en":
            translated = text
            return TranslationResult(original=text, translated=translated, language=language, translated_source=False)

        try:
            # Translate only non-code text, then restore code blocks.
            if self.mode == "api_key":
                translated = self._translate_api(masked)
            else:
                result = self.client.translate(masked, target_language="en")
                translated = result.get("translatedText", masked) if isinstance(result, dict) else masked

            for idx, block in enumerate(code_blocks):
                translated = translated.replace(f"__CODE_BLOCK_{idx}__", block)
            return TranslationResult(original=text, translated=translated, language=language, translated_source=True)
        except Exception as exc:
            logger.warning("Translation failed: %s", exc)
            return TranslationResult(original=text, translated=text, language=language, translated_source=False)

    def _detect_language_api(self, text: str) -> str:
        if not self.api_key or not self.rest_client:
            return "unknown"
        try:
            resp = self.rest_client.post(
                "https://translation.googleapis.com/language/translate/v2/detect",
                data={"q": text, "key": self.api_key}
            )
            resp.raise_for_status()
            data = resp.json()
            detections = data.get("data", {}).get("detections", [])
            if detections and detections[0]:
                return detections[0][0].get("language", "unknown")
        except Exception as exc:
            logger.warning("Language detection failed: %s", exc)
        return "unknown"

    def _translate_api(self, text: str) -> str:
        if not self.api_key or not self.rest_client:
            return text
        resp = self.rest_client.post(
            "https://translation.googleapis.com/language/translate/v2",
            data={"q": text, "target": "en", "key": self.api_key}
        )
        resp.raise_for_status()
        data = resp.json()
        translated = data.get("data", {}).get("translations", [{}])[0].get("translatedText", text)
        return html.unescape(translated)


def update_language_stats(stats: Dict, language: str, translated: bool):
    if not language:
        language = "unknown"
    stats["language_distribution"][language] = stats["language_distribution"].get(language, 0) + 1
    if translated:
        stats["translated_artifact_count"] += 1