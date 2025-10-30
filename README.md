# 🤖 AI Chatbot API

API profesional de chatbot con Inteligencia Artificial usando Claude (Anthropic), lista para integrar en cualquier aplicación web o móvil. Incluye logging para fácil depuración y validación robusta de API key.

**Desarrollado por Jorge Lago Campos** | [LinkedIn](https://www.linkedin.com/in/jorge-lago-campos/) | [GitHub](https://github.com/Leikymain)

## 🚀 Características

- ✅ **Multi-cliente**: Configura diferentes chatbots para distintos negocios
- ✅ **Context-aware**: Mantiene el contexto de la conversación por sesión/cliente
- ✅ **Personalizable**: Prompts de sistema únicos por cliente y configurables vía API
- ✅ **Endpoints claros**: `/chat`, `/chat/simple`, `/clients`, `/health`
- ✅ **Logs automáticos**: Mensajes debug para puntos de fallo en producción
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

# Configura tu API key
echo "ANTHROPIC_API_KEY=tu_api_key_aqui" > .env

# Ejecuta la API
python main.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Uso

### Swagger interactivo

Abre `http://localhost:8000/docs` para probar la API.

### Ejemplo básico

```bash
curl -X POST "http://localhost:8000/chat/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿en qué me puedes ayudar?",
    "client_id": "demo"
  }'
```

### Ejemplo avanzado con contexto

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
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

- `POST /chat`  
  Conversa manteniendo historial/contexto.
- `POST /chat/simple`  
  Envío ultra-sencillo, un mensaje, respuesta directa.
- `GET /clients`  
  Lista los clientes configurados.
- `GET /health`  
  Prueba de salud del servicio.

## ⚙️ Dependencias principales

- `fastapi==0.109.0`
- `uvicorn==0.27.0`
- `anthropic==0.21.3`
- `httpx==0.27.2`
- `pydantic==2.6.0`
- `python-dotenv==1.0.0`

Asegúrate que tu `requirements.txt` refleja estas versiones.

## 💡 Personalización

### Añadir log/depuración

Ya está incluido `logging`, ajusta nivel desde el propio código si necesitas más detalle.

### Añadir clientes

Edita el diccionario `CLIENT_CONFIGS` en `main.py`:

```python
CLIENT_CONFIGS["nuevo"] = {
    "name": "Tu Negocio",
    "system_prompt": "¿Cómo debería comportarse el bot?",
    "max_tokens": 900
}
```

### Cambiar modelo

Modifica la key `"model"` en la llamada a `client.messages.create` (por ejemplo `"claude-sonnet-4-5-20250929"`).


## 🤝 Contribuye

Las PR y los issues son bienvenidos.

## 📄 Licencia

MIT License - Listo para proyectos comerciales.

---
