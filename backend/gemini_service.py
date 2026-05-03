import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define the persona/instructions for the assistant
SYSTEM_PROMPT = """You are a helpful, neutral, and educational assistant designed to explain the election process. 
Your goal is to help users understand election timelines, steps, and procedures in an interactive and easy-to-follow way.
Provide clear, concise, and accurate information. If a user asks a question not related to elections or civics, 
politely decline to answer and guide them back to the topic of elections. Do not show any political bias."""

# Initialize the model with the system instruction if supported, 
# otherwise we will prepend it to the chat history.
# Using gemini-pro for text tasks.
model = genai.GenerativeModel('gemini-pro')

# Initialize a chat session to maintain context (optional, but good for interactive assistants)
# For a stateless API, we can just generate content. Let's make it stateless for simplicity and scalability,
# but we'll include the system prompt as context.

async def get_gemini_response(user_message: str) -> str:
    try:
        # Prepend the system prompt for context in a stateless call
        prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error communicating with Gemini: {e}")
        return "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again later."
