from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    Pydantic model representing the incoming chat request.
    Enforces strict string lengths to prevent giant payload attacks.
    """
    message: str = Field(
        ..., 
        description="The user's message to the election assistant.", 
        min_length=1,
        max_length=1000 # Strict limit to prevent abuse/buffer overflows
    )

class ChatResponse(BaseModel):
    """
    Pydantic model representing the assistant's reply.
    """
    reply: str = Field(..., description="The assistant's reply.")
