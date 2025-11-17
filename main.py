from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import os
import time
import logging
from auth_middleware import require_auth

load_dotenv()

# Logger
ENV_AUTH_TOKEN = os.getenv("API_TOKEN") or os.getenv("API_TOKEN")
logger = logging.getLogger("chatbot-api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
if not ENV_AUTH_TOKEN:
    logger.warning("⚠️ Token de entorno no configurado")

ALLOWED_ORIGINS = [
    "https://automapymes.com",
    "https://www.automapymes.com",
    "https://*.automapymes.com"
]

app = FastAPI(
    title="AI Chatbot API",
    description="API profesional de chatbot con IA - By Jorge Lago",
    version="1.1.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# RATE LIMIT
# =========================
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 30))
RATE_WINDOW = 60
request_timestamps = {}

def check_rate_limit(client_ip: str):
    now = time.time()
    timestamps = request_timestamps.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < RATE_WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        raise HTTPException(429, "Demasiadas peticiones. Espera un minuto.")

    timestamps.append(now)
    request_timestamps[client_ip] = timestamps

# =========================
# MODELOS
# =========================
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    client_id: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    tokens_used: int
    timestamp: str

CLIENT_CONFIGS = {
    "demo": {"name": "Demo Client", "system_prompt": "Eres un asistente amigable.", "max_tokens": 1024},
    "ecommerce": {"name": "E-commerce Assistant", "system_prompt": "Ayudas con productos y pedidos.", "max_tokens": 800},
    "soporte": {"name": "Tech Support Bot", "system_prompt": "Respondes sobre problemas técnicos.", "max_tokens": 1500}
}

# =========================
# ENDPOINTS PÚBLICOS
# =========================
@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/demo")

@app.get("/demo", include_in_schema=False)
def serve_demo():
    with open("static/demo.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/auth/check")
async def auth_check(token: str = Depends(require_auth)):
    """Verifica si el token en header es válido (para el modal)."""
    return {"valid": True}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/clients")
def list_clients():
    return {"clients": list(CLIENT_CONFIGS.keys()), "configs": CLIENT_CONFIGS}

# =========================
# ENDPOINTS PROTEGIDOS
# =========================
@app.post("/chat")
async def chat(request: ChatRequest, req: Request, token: str = Depends(require_auth)):
    check_rate_limit(req.client.host)

    if request.client_id not in CLIENT_CONFIGS:
        raise HTTPException(404, "Cliente no encontrado")

    client_config = CLIENT_CONFIGS[request.client_id]
    system_prompt = request.system_prompt or client_config["system_prompt"]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "Falta ANTHROPIC_API_KEY")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=request.max_tokens or client_config["max_tokens"],
            temperature=request.temperature,
            system=system_prompt,
            messages=messages
        )

        return ChatResponse(
            response=response.content[0].text,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(500, f"Error inesperado: {str(e)}")

@app.post("/chat/simple")
async def simple_chat(message: str, req: Request, client_id: str = "demo", token: str = Depends(require_auth)):
    request = ChatRequest(messages=[Message(role="user", content=message)], client_id=client_id)
    return await chat(request, req)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
