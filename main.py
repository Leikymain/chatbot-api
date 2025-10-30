from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import anthropic
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Chatbot API",
    description="API profesional de chatbot con IA - By Jorge Lago",
    version="1.0.0"
)

# CORS para permitir llamadas desde cualquier frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class Message(BaseModel):
    role: str  # "user" o "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    client_id: str  # Identificador del cliente
    system_prompt: Optional[str] = None  # Personalización por cliente
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    tokens_used: int
    timestamp: str

# Configuración de clientes (esto iría en BD en producción)
CLIENT_CONFIGS = {
    "demo": {
        "name": "Demo Client",
        "system_prompt": "Eres un asistente amigable y profesional. Respondes de forma concisa y útil.",
        "max_tokens": 1024
    },
    "ecommerce": {
        "name": "E-commerce Assistant",
        "system_prompt": "Eres un asistente de tienda online. Ayudas con productos, pedidos y devoluciones. Siempre eres cortés y orientado a ventas.",
        "max_tokens": 800
    },
    "soporte": {
        "name": "Tech Support Bot",
        "system_prompt": "Eres un asistente técnico. Respondes preguntas sobre software y troubleshooting. Eres paciente y detallado.",
        "max_tokens": 1500
    }
}

API_TOKEN = os.getenv("API_TOKEN", None)

@app.middleware("http")
async def verify_token(request: Request, call_next):
    """
    Middleware que protege todos los endpoints excepto la documentación y la raíz.
    """
    if request.url.path in ["/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el header Authorization: Bearer <token>"
        )
    provided_token = token.split("Bearer ")[1]
    if API_TOKEN is None or provided_token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o no autorizado"
        )
    return await call_next(request)

@app.get("/")
def root():
    return {
        "message": "AI Chatbot API - Activa",
        "docs": "/docs",
        "version": "1.0.0",
        "developer": "Jorge Lago Campos"
    }

@app.get("/clients")
def list_clients():
    """Lista los clientes configurados disponibles"""
    return {
        "clients": list(CLIENT_CONFIGS.keys()),
        "configs": CLIENT_CONFIGS
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal del chatbot.
    
    Envía mensajes y recibe respuestas de IA.
    Mantiene contexto mediante el historial de mensajes.
    """
    
    # Validar cliente
    if request.client_id not in CLIENT_CONFIGS:
        raise HTTPException(
            status_code=404, 
            detail=f"Cliente '{request.client_id}' no encontrado. Usa /clients para ver disponibles."
        )
    
    client_config = CLIENT_CONFIGS[request.client_id]
    
    # System prompt: usa el personalizado del request o el del cliente
    system_prompt = request.system_prompt or client_config["system_prompt"]
    
    # Validar API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="API key no configurada. Establece ANTHROPIC_API_KEY en tu archivo .env"
        )
    
    try:

        # Inicializar cliente de Anthropic (versión 0.21.3)
        
        client = anthropic.Anthropic(api_key=api_key)

        
        # Convertir mensajes al formato de Anthropic
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Llamar a la API
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
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

@app.post("/chat/simple")
async def simple_chat(
    message: str,
    client_id: str = "demo"
):
    """
    Endpoint simplificado para testing rápido.
    Envía un mensaje único sin contexto.
    """
    request = ChatRequest(
        messages=[Message(role="user", content=message)],
        client_id=client_id
    )
    return await chat(request)

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)