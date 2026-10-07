import httpx
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings

logger = logging.getLogger("sla_predict.llm")

class ClaudeClient:
    @staticmethod
    async def generate_explanation(prompt: str) -> Optional[str]:
        """
        Sends prompt to Anthropic Claude API server-side.
        Returns generated explanation text, or None if key is absent / call fails.
        """
        if not settings.ANTHROPIC_API_KEY:
            logger.debug("ANTHROPIC_API_KEY not configured. Using deterministic explanation generator.")
            return None

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    content_blocks = data.get("content", [])
                    if content_blocks and "text" in content_blocks[0]:
                        return content_blocks[0]["text"]
                else:
                    logger.warning("Claude API returned non-200 status (%d): %s", resp.status_code, resp.text[:100])
        except Exception as e:
            logger.warning("Failed communicating with Claude API: %s", e)
        return None
