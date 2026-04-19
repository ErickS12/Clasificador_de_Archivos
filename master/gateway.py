"""
API Gateway
La API Gateway es el punto de entrada para los clientes. Recibe las solicitudes de clasificación, valida los archivos PDF y luego mandan el procesamiento a los workers a través del módulo de consenso. También se encarga de registrar cada operación para monitoreo y debugging.
En esta fase, se implementa la API Gateway con FastAPI, incluyendo:
- Endpoints para recibir archivos PDF y áreas de interés.
- Validación de archivos (tipo y tamaño).
- Logging de cada solicitud y su resultado.
- Manejo de errores y respuestas adecuadas para el cliente.
"""

from fastapi import HTTPException, UploadFile
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

TAM_MAX_ARCHIVOS_MB    = 10
TAM_MAX_ARCHIVOS_BYTES = TAM_MAX_ARCHIVOS_MB * 1024 * 1024


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        inicio   = time.time()
        response = await call_next(request)
        transcurrido  = round(time.time() - inicio, 3)
        print(f"[GATEWAY] {request.method} {request.url.path} → {response.status_code} ({transcurrido}s)")
        return response


def validar_carga(archivo: UploadFile):
    """Valida que el archivo sea PDF y no supere el tamaño máximo."""
    if not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    if archivo.size and archivo.size > TAM_MAX_ARCHIVOS_BYTES:
        raise HTTPException(status_code=413, detail=f"El archivo supera el límite de {TAM_MAX_ARCHIVOS_MB} MB.")
