from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message to the election assistant.", min_length=1)

class ChatResponse(BaseModel):
    reply: str = Field(..., description="The assistant's reply.")
