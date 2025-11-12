from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import os
import time
import logging
from auth_middleware import require_auth
from fastapi import Depends

load_dotenv()

# Aviso genérico si falta token de entorno (compatibilidad con Railway)
ENV_AUTH_TOKEN = os.getenv("API_TOKEN") or os.getenv("AUTH_TOKEN")
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

# CORS para permitir llamadas desde dominios de producción autorizados
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 🔐 AUTENTICACIÓN POR TOKEN
# =========================

API_TOKEN = os.getenv("API_TOKEN")
security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependencia para proteger endpoints mediante Bearer Token.
    También activa el botón 'Authorize' en Swagger (/docs).
    """
    if not API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_TOKEN no configurado en el servidor"
        )
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el header Authorization: Bearer <token>"
        )
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o no autorizado"
        )
    return True


# =================================
# ⚙️ RATE LIMITING (ANTI-ABUSO SIMPLE)
# =================================

RATE_LIMIT = int(os.getenv("RATE_LIMIT", 30))  # peticiones por minuto
RATE_WINDOW = 60  # segundos
request_timestamps = {}

def check_rate_limit(client_ip: str):
    """
    Limita peticiones por IP para evitar abuso de la API (protege tus créditos).
    """
    now = time.time()
    timestamps = request_timestamps.get(client_ip, [])
    # Mantener solo las peticiones en la última ventana de tiempo
    timestamps = [t for t in timestamps if now - t < RATE_WINDOW]
    if len(timestamps) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas peticiones. Espera un minuto antes de volver a intentar."
        )
    timestamps.append(now)
    request_timestamps[client_ip] = timestamps


# ==========================
# 🧠 MODELOS Y CONFIG CLIENTES
# ==========================

class Message(BaseModel):
    role: str  # "user" o "assistant"
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
    "demo": {
        "name": "Demo Client",
        "system_prompt": "Eres un asistente amigable y profesional. Respondes de forma concisa y útil.",
        "max_tokens": 1024
    },
    "ecommerce": {
        "name": "E-commerce Assistant",
        "system_prompt": "Eres un asistente de tienda online. Ayudas con productos, pedidos y devoluciones.",
        "max_tokens": 800
    },
    "soporte": {
        "name": "Tech Support Bot",
        "system_prompt": "Eres un asistente técnico. Respondes preguntas sobre software y troubleshooting.",
        "max_tokens": 1500
    }
}


# ======================
# 🌐 ENDPOINTS PÚBLICOS
# ======================

@app.get("/")
def root():
    return {
        "message": "AI Chatbot API - Activa",
        "docs": "/docs",
        "version": "1.1.0",
        "developer": "Jorge Lago Campos"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/clients")
def list_clients():
    """Lista los clientes configurados disponibles"""
    return {"clients": list(CLIENT_CONFIGS.keys()), "configs": CLIENT_CONFIGS}


# ======================
# 💬 ENDPOINTS PROTEGIDOS
# ======================

# endpoint /chat sin dependencia de verify_token, mantiene rate limit
@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_token)])
async def chat(request: ChatRequest, req: Request,token: str = Depends(require_auth)):
    """
    Endpoint principal del chatbot.
    Protegido con token y rate limit.
    """
    check_rate_limit(req.client.host)

    if request.client_id not in CLIENT_CONFIGS:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    client_config = CLIENT_CONFIGS[request.client_id]
    system_prompt = request.system_prompt or client_config["system_prompt"]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Falta ANTHROPIC_API_KEY")

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

    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error de API de Anthropic: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


# endpoint /chat/simple sin dependencia de verify_token
@app.post("/chat/simple", dependencies=[Depends(verify_token)])
async def simple_chat(message: str, req: Request, client_id: str = "demo",token: str = Depends(require_auth)):
    """
    Endpoint simplificado para pruebas rápidas.
    Protegido con token y limitación de peticiones.
    """
    request = ChatRequest(messages=[Message(role="user", content=message)], client_id=client_id)
    return await chat(request, req)


# ======================
# 🧩 EJECUCIÓN LOCAL
# ======================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
