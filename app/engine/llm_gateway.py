import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types

from ..config import settings

logger = logging.getLogger(__name__)


async def call_llm(prompt: str) -> str:
    """
    Call Google's Gemini using the google-genai SDK.
    """
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is required for Gemini provider")

    try:
        # Initialize client with API key
        client = genai.Client(api_key=api_key)

        model_name = settings.AI_MODEL.strip()
        # Ensure model identifier format is consistent
        if model_name.startswith("models/"):
            model_name = model_name.replace("models/", "")

        # Asynchronously generate content
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        if not response or not response.text:
            raise ValueError("Empty response received from Gemini API")

        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise Exception(f"Gemini API error: {str(e)}")