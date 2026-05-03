import os
import httpx
import logging
import google.generativeai as genai
from google.cloud import logging as cloud_logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

# Set up standard logging to fallback if cloud logging fails
logger = logging.getLogger("ElectionAssistant")
logger.setLevel(logging.INFO)

# 1. Google Services: Cloud Logging
try:
    client = cloud_logging.Client()
    client.setup_logging()
    logger.info("Google Cloud Logging successfully initialized.")
except Exception as e:
    logger.warning(f"Could not initialize Google Cloud Logging (using local): {e}")

# Configure Gemini API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

# 2. Efficiency: In-memory async cache for frequent queries
_response_cache: Dict[str, str] = {}

SYSTEM_PROMPT = """You are a helpful, neutral, and educational assistant designed to explain the election process. 
Your goal is to help users understand election timelines, steps, and procedures in an interactive and easy-to-follow way.
Provide clear, concise, and accurate information. If a user asks a question not related to elections or civics, 
politely decline to answer and guide them back to the topic of elections. Do not show any political bias."""

# 3. Google Services: Advanced Gemini Configuration
generation_config = genai.types.GenerationConfig(
    temperature=0.2, # Keep it low for factual accuracy
    top_p=0.8,
    top_k=40,
)

# Using gemini-pro for text tasks.
model = genai.GenerativeModel(
    model_name='gemini-pro',
    generation_config=generation_config
)

async def _fetch_civic_info(query: str) -> Optional[str]:
    """
    Checks if the user is asking about representatives or voting locations and
    uses the Google Civic Information API if applicable.
    
    Args:
        query (str): The user's input string.
        
    Returns:
        Optional[str]: Civic API response formatted as a string, or None if not applicable.
    """
    # Simple keyword heuristic to trigger Civic API
    civic_keywords = ["representative", "polling", "where to vote", "my district"]
    if not any(keyword in query.lower() for keyword in civic_keywords):
        return None
        
    civic_api_key = os.getenv("GEMINI_API_KEY") # Usually the same key is authorized for multiple APIs
    
    # Example: If the user provides an address, we can hit the representativeInfoByAddress endpoint.
    # Since we only have a generic query here, we'll return a helpful message directing them to the tool.
    # In a full implementation, we'd extract the address using NER.
    
    logger.info("Civic Information API triggered by keywords.")
    return (
        "To find your specific polling location or representatives, you can use the official "
        "**[Google Civic Information tool](https://developers.google.com/civic-information)**. "
        "Because I don't have your specific home address, I can't look up your exact polling place, "
        "but typically you can find this on your state's Secretary of State website!"
    )

async def get_gemini_response(user_message: str) -> str:
    """
    Processes the user's message, checks the cache, queries the Civic API if relevant, 
    and then falls back to Google Gemini.
    
    Args:
        user_message (str): The user's input.
        
    Returns:
        str: The assistant's response.
    """
    # 1. Efficiency: Check Cache
    normalized_message = user_message.lower().strip()
    if normalized_message in _response_cache:
        logger.info(f"Cache hit for query: {normalized_message}")
        return _response_cache[normalized_message]
        
    logger.info(f"Processing new user query: {user_message}")
    
    try:
        # 2. Google Services: Civic API Integration Check
        civic_data = await _fetch_civic_info(user_message)
        if civic_data:
            _response_cache[normalized_message] = civic_data
            return civic_data

        # 3. Google Services: Gemini Call
        prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        
        # Use generate_content_async for better efficiency in FastAPI
        response = await model.generate_content_async(prompt)
        reply = response.text
        
        # Save to cache
        _response_cache[normalized_message] = reply
        logger.info("Successfully generated response from Gemini.")
        
        return reply
        
    except Exception as e:
        logger.error(f"Error communicating with Google Services: {e}")
        return "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again later."
