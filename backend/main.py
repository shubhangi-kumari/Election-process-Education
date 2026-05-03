from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

from .models import ChatRequest, ChatResponse
from .gemini_service import get_gemini_response

# Rate Limiting configuration
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Election Process Assistant API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 1. Efficiency: GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. Security: Strict CORS
# For a hackathon, we assume the frontend might be hosted on the same domain, 
# or specific origins. Using the Cloud Run URL pattern.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://election-assistant-*.a.run.app"  # Pattern for Cloud Run
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# 3. Security: HTTP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # Basic Content-Security-Policy
    # Note: If DOMPurify is loaded from CDN, we must allow it.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://www.googleapis.com;"
    )
    return response

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_endpoint(chat_req: ChatRequest, request: Request) -> ChatResponse:
    """
    Chat endpoint to process user queries securely.
    Rate limited to 20 requests per minute per IP.
    """
    if not chat_req.message or not chat_req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get response from Gemini service
    reply = await get_gemini_response(chat_req.message)
    return ChatResponse(reply=reply)

@app.get("/api/health")
@limiter.limit("60/minute")
async def health_check(request: Request) -> dict[str, str]:
    """Health check endpoint to verify API status."""
    return {"status": "healthy"}

# Serve the frontend files securely
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
