import asyncio
import httpx
import os
import json
import logging

# Set up simple logging for the module
logger = logging.getLogger(__name__)

from core.prompts import (PROMPT_ARCHAEOLOGY, PROMPT_WHY_QUERY, 
                           PROMPT_ASSUMPTION_ALARM, PROMPT_ONBOARDING)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL_NAME = "mistral-large-latest"
MISTRAL_FALLBACK_MODEL = "mistral-small-latest"
GEMINI_MODEL_NAME = MISTRAL_MODEL_NAME  # Backwards compatibility alias
GEMINI_MODEL_DISPLAY_NAME = "Gemini 2.5 pro"
MAX_PROMPT_CHARS = 20000

class GeminiClient:

    def __init__(self):
        self.api_key = os.environ.get("MISTRAL", "").strip()
        if not self.api_key:
            raise ValueError("MISTRAL environment variable is not set")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def analyze_repository(self, archaeology_context: str) -> dict:
        prompt = PROMPT_ARCHAEOLOGY.format(archaeology_context=archaeology_context)
        try:
            response = await self._generate_content(prompt)
            return self._safe_parse_json(response)
        except Exception as e:
            logger.error(f"Error in analyze_repository: {e}", exc_info=True)
            return {"error": "gemini_failed", "detail": str(e)}

    async def answer_query(self, repo_url: str, 
                           knowledge_core: dict, question: str) -> dict:
        prompt = PROMPT_WHY_QUERY.format(
            repo_url=repo_url,
            knowledge_core_json=json.dumps(knowledge_core),
            question=question
        )
        try:
            response = await self._generate_content(prompt)
            return self._safe_parse_json(response)
        except Exception as e:
            logger.error(f"Error in answer_query: {e}", exc_info=True)
            return {"error": "gemini_failed", "detail": str(e)}

    async def check_alarm(self, repo_url: str, 
                          assumptions: list, code_snippet: str) -> dict:
        prompt = PROMPT_ASSUMPTION_ALARM.format(
            repo_url=repo_url,
            assumptions_json=json.dumps(assumptions),
            code_snippet=code_snippet
        )
        try:
            response = await self._generate_content(prompt)
            return self._safe_parse_json(response)
        except Exception as e:
            logger.error(f"Error in check_alarm: {e}", exc_info=True)
            return {"error": "gemini_failed", "detail": str(e)}

    async def generate_onboarding(self, repo_url: str, 
                                   knowledge_core: dict, 
                                   feature: str) -> dict:
        prompt = PROMPT_ONBOARDING.format(
            repo_url=repo_url,
            knowledge_core_json=json.dumps(knowledge_core),
            feature_description=feature
        )
        try:
            response = await self._generate_content(prompt)
            return self._safe_parse_json(response)
        except Exception as e:
            logger.error(f"Error in generate_onboarding: {e}", exc_info=True)
            return {"error": "gemini_failed", "detail": str(e)}

    async def _generate_content(self, prompt: str):
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n... (truncated for NVIDIA request limits)"
        response = await self._call_mistral_api(prompt, MISTRAL_MODEL_NAME)
        if response.strip():
            return response

        # Fallback: smaller model + shorter prompt to avoid empty responses
        short_prompt = prompt[:8000] + "\n\n... (shortened for fallback)"
        response = await self._call_mistral_api(short_prompt, MISTRAL_FALLBACK_MODEL)
        return response

    async def _call_mistral_api(self, prompt: str, model_name: str) -> str:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Return ONLY valid JSON. No markdown. No extra text."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 512,
            "temperature": 0.2,
            "top_p": 0.7,
            "stream": False,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(MISTRAL_API_URL, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            logger.error("Mistral API timeout")
            raise ValueError("API timeout")
        except httpx.HTTPStatusError as exc:
            logger.error(f"Mistral API error: {exc.response.status_code} {exc.response.text}")
            raise ValueError(str(exc))
        except httpx.HTTPError as exc:
            logger.error(f"Mistral API error: {exc}")
            raise ValueError(str(exc))

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0].get("message", {}).get("content", "")
        return ""

    def _safe_parse_json(self, text: str) -> dict:
        logger.warning("NVIDIA raw output preview: %s", text[:800])
        text = text.strip()
        
        # Strip potential markdown fences
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Attempt 1: Direct parse
        try:
            parsed = json.loads(text)
            logger.debug("Successfully parsed JSON on Attempt 1")
            return parsed
        except json.JSONDecodeError:
            pass
            
        # Attempt 2: Extract substring
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                substring = text[start_idx:end_idx+1]
                parsed = json.loads(substring)
                logger.debug("Successfully parsed JSON on Attempt 2 (substring)")
                return parsed
        except json.JSONDecodeError:
            pass
        
        # Attempt 3: Try to complete truncated JSON
        try:
            start_idx = text.find('{')
            if start_idx != -1:
                substring = text[start_idx:]
                # Count open/close braces
                open_count = substring.count('{')
                close_count = substring.count('}')
                if open_count > close_count:
                    substring = substring + ('}' * (open_count - close_count))
                parsed = json.loads(substring)
                logger.debug("Successfully parsed JSON on Attempt 3 (completion)")
                return parsed
        except json.JSONDecodeError:
            pass
            
        # Fallback
        logger.warning(f"Failed to parse JSON. Raw preview: {text[:500]}")
        return {"parse_error": True, "raw_preview": text[:500]}