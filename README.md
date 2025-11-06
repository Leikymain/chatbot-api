# 🤖 AI Chatbot API

API profesional de chatbot con Inteligencia Artificial usando Claude (Anthropic), lista para integrar en cualquier aplicación web o móvil. Incluye logging para fácil depuración, autenticación por Bearer Token y limitación de peticiones para proteger tus créditos.

**Desarrollado por Jorge Lago Campos** | [LinkedIn](https://www.linkedin.com/in/jorge-lago-campos/) | [GitHub](https://github.com/Leikymain)

## 🚀 Características

- ✅ **Multi-cliente**: Configura diferentes chatbots para distintos negocios
- ✅ **Context-aware**: Mantiene el contexto de la conversación por sesión/cliente
- ✅ **Personalizable**: Prompts de sistema únicos por cliente y configurables vía API
- ✅ **Endpoints claros**: `/chat`, `/chat/simple`, `/clients`, `/health`
- ✅ **Autenticación Bearer Token**: Protección simple + soporte de "Authorize" en Swagger
- ✅ **Rate limiting**: Límite de peticiones configurable por IP para evitar abuso
- ✅ **Swagger UI**: Documentación automática en `/docs`
- ✅ **Productivo**: Código listo para escalar e integrar

## 📋 Casos de Uso

- Atención al cliente 24/7
- Asistente de e-commerce
- Soporte técnico automatizado
- Bot de FAQ
- Asistente virtual personalizado

## 🛠️ Instalación Local

```bash
# Clona el repositorio
git clone https://github.com/Leikymain/chatbot-api.git
cd chatbot-api

# Crea y activa un entorno virtual
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Unix/MacOS:
source venv/bin/activate

# Instala dependencias exactas
pip install -r requirements.txt

# Configura variables en .env
# Clave de Anthropic y token de acceso para la API
# RATE_LIMIT es opcional (peticiones por minuto, por IP). Default: 30
(echo ANTHROPIC_API_KEY=tu_api_key_aqui & echo API_TOKEN=tu_token_superseguro & echo RATE_LIMIT=30) > .env

# Ejecuta la API
python main.py
```

La API estará disponible en: `http://localhost:8000`

## 🔐 Autenticación y entorno

El servicio obtiene automáticamente sus tokens desde variables de entorno privadas (Railway, Docker, etc.). No es necesario introducir tokens desde el frontend ni en Swagger.

Los endpoints protegidos requieren Bearer Token. En Swagger (`/docs`) puedes usar el botón "Authorize".

- Define tu token en `.env`:

```env
API_TOKEN=tu_token_superseguro
```

- Envía el header `Authorization: Bearer <token>`:

### Ejemplo cURL (sin enviar Authorization desde cliente)
```bash
curl -X POST "http://localhost:8000/chat/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿en qué me puedes ayudar?",
    "client_id": "demo"
  }'
```

### Ejemplo Python (requests)

```python
import requests

headers = {
    "Authorization": "Bearer tu_token_superseguro",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/chat/simple",
    headers=headers,
    json={
        "message": "Hola, ¿en qué me puedes ayudar?",
        "client_id": "demo"
    }
)
print(response.json())
```

## 📚 Uso

### Swagger interactivo

Abre `http://localhost:8000/docs` para probar la API. Pulsa **Authorize** e introduce `Bearer tu_token_superseguro` para habilitar llamadas desde la UI.

### Ejemplo avanzado con contexto

```python
import requests

headers = {"Authorization": "Bearer tu_token_superseguro"}

response = requests.post(
    "http://localhost:8000/chat",
    headers=headers,
    json={
        "client_id": "ecommerce",
        "messages": [
            {"role": "user", "content": "¿Tienen envío gratis?"},
            {"role": "assistant", "content": "¡Sí! Envío gratis por pedidos mayores a 50€."},
            {"role": "user", "content": "¿Y cuánto tarda el envío?"}
        ]
    }
)
print(response.json()["response"])
```

## 🎯 Endpoints

### Públicos

- `GET /` – Estado básico y metadatos del servicio
- `GET /health` – Health check
- `GET /clients` – Lista de clientes configurados

### Protegidos (requieren Bearer Token)

- `POST /chat` – Conversación con contexto, configurable por cliente
- `POST /chat/simple` – Mensaje único para pruebas rápidas

## 🐳 Deploy con Docker

### Opción A: Docker CLI

```bash
# Construir imagen
docker build -t chatbot-api:latest .

# Ejecutar contenedor (puerto 8000 por defecto)
docker run --rm -p 8000:8000 \
  -e ANTHROPIC_API_KEY=tu_api_key_aqui \
  -e API_TOKEN=tu_token_superseguro \
  -e RATE_LIMIT=30 \
  --name chatbot-api chatbot-api:latest
```

### Opción B: docker-compose

Crea un archivo `docker-compose.yml`:

```yaml
services:
  api:
    build: .
    image: chatbot-api:latest
    container_name: chatbot-api
    ports:
      - "8000:8000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      API_TOKEN: ${API_TOKEN}
      RATE_LIMIT: ${RATE_LIMIT:-30}
    restart: unless-stopped
```

Luego:

```bash
docker compose up -d --build
```

### Consejos de producción

- Restringe CORS a tus dominios: `allow_origins=["https://tu-dominio.com"]`.
- Mantén el `API_TOKEN` en un secreto seguro (no lo subas al repo).
- Usa logging centralizado y métricas (Prometheus, ELK, etc.).
- Añade un proxy inverso (Nginx) si necesitas TLS/HTTP2/compresión.

## ⚙️ Dependencias principales

- `fastapi==0.109.0`
- `uvicorn==0.27.0`
- `anthropic==0.21.3`
- `httpx==0.27.2`
- `pydantic==2.6.0`
- `python-dotenv==1.0.0`

Asegúrate que tu `requirements.txt` refleja estas versiones.

## 🚦 Rate Limiting

El sistema de anti-abuso limita peticiones por IP.

- Variable `.env`: `RATE_LIMIT` (por defecto `30`) – número de peticiones permitidas por minuto
- Respuesta en caso de exceso: `429 Demasiadas peticiones`

## 💡 Personalización

### Añadir clientes

Edita el diccionario `CLIENT_CONFIGS` en `main.py`:

```python
CLIENT_CONFIGS["nuevo"] = {
    "name": "Tu Negocio",
    "system_prompt": "¿Cómo debería comportarse el bot?",
    "max_tokens": 900
}
```

### Cambiar modelo de IA

Modifica la key `"model"` en la llamada a `client.messages.create` (por ejemplo `"claude-sonnet-4-5-20250929"`).

## 🗺️ Roadmap

- [ ] Autenticación JWT con roles/claims
- [ ] Persistencia de historial en BD (SQL/NoSQL)
- [ ] Configuración de clientes en BD con panel admin
- [ ] Métricas y trazas (OpenTelemetry)
- [ ] Cache de respuestas/embeddings
- [ ] Streaming de respuestas (Server-Sent Events/WebSocket)
- [ ] Webhooks y colas para tareas asíncronas
- [ ] CI/CD con tests y quality gates

## 🤝 Contribuye

Las PR y los issues son bienvenidos.

## 📄 Licencia

MIT License - Listo para proyectos comerciales.

---
