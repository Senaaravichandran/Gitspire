import google.generativeai as genai
import os
import json
import logging

# Set up simple logging for the module
logger = logging.getLogger(__name__)

from core.prompts import (PROMPT_ARCHAEOLOGY, PROMPT_WHY_QUERY, 
                           PROMPT_ASSUMPTION_ALARM, PROMPT_ONBOARDING)

GEMINI_MODEL_NAME = "models/gemini-2.5-pro"
GEMINI_MODEL_DISPLAY_NAME = "Gemini 2.5 Pro"

class GeminiClient:

    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.8,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json"
            }
        )

    async def analyze_repository(self, archaeology_context: str) -> dict:
        prompt = PROMPT_ARCHAEOLOGY.format(archaeology_context=archaeology_context)
        try:
            # generate_content_async is not reliably available in all versions, 
            # using run_in_executor to ensure non-blocking if needed, or await directly if available.
            # We'll use generate_content_async as requested.
            response = await self.model.generate_content_async(prompt)
            
            # Log token usage
            if hasattr(response, 'usage_metadata'):
                logger.info(f"Token usage for analyze_repository: {response.usage_metadata}")
            
            return self._safe_parse_json(response.text)
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
            response = await self.model.generate_content_async(prompt)
            return self._safe_parse_json(response.text)
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
            response = await self.model.generate_content_async(prompt)
            return self._safe_parse_json(response.text)
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
            response = await self.model.generate_content_async(prompt)
            return self._safe_parse_json(response.text)
        except Exception as e:
            logger.error(f"Error in generate_onboarding: {e}", exc_info=True)
            return {"error": "gemini_failed", "detail": str(e)}

    def _safe_parse_json(self, text: str) -> dict:
        text = text.strip()
        
        # Strip potential markdown fences just in case model ignores instruction
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Attempt 1
        try:
            parsed = json.loads(text)
            logger.debug("Successfully parsed JSON on Attempt 1")
            return parsed
        except json.JSONDecodeError:
            pass
            
        # Attempt 2
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
            
        # Attempt 3
        logger.warning(f"Failed to parse JSON. Raw preview: {text[:500]}")
        return {"parse_error": True, "raw_preview": text[:500]}