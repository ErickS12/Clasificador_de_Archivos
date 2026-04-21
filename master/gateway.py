"""

API GATEWAY


PROPÓSITO:
  Punto de entrada central del sistema distribuido de clasificación.
  Valida solicitudes, registra operaciones y coordina con workers.

RESPONSABILIDADES:
  1. Validación de archivos (tipo PDF + tamaño máximo)
  2. Logging/monitoreo de todas las solicitudes HTTP
  3. Manejo centralizado de errores
  4. Integración con módulo de consenso (consensus.py)

HERRAMIENTAS UTILIZADAS:
  - FastAPI: Framework para construir APIs REST
  - Starlette: Middleware base (BaseHTTPMiddleware)
  - Python time: Medir duración de requests
  - HTTPException: Errores HTTP estándar


| Código | Causa | Solución |
|---|---|---|
| **400** | No es PDF | Valida que sea `.pdf` |
| **413** | Archivo > 10 MB | Comprime el PDF o divide en partes |
| **500** | Error interno | Revisa que workers estén corriendo |
"""

from fastapi import HTTPException, UploadFile
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

TAM_MAX_ARCHIVOS_MB    = 10  # Límite de tamaño de archivos (en MB)
TAM_MAX_ARCHIVOS_BYTES = TAM_MAX_ARCHIVOS_MB * 1024 * 1024  # Conversión a bytes


class LoggingMiddleware(BaseHTTPMiddleware):

    
    async def dispatch(self, request: Request, call_next):
        # Captura tiempo de inicio
        inicio = time.time()
        # Ejecuta la solicitud real (endpoint)
        response = await call_next(request)
        # Calcula tiempo transcurrido
        transcurrido = round(time.time() - inicio, 3)
        # Registra: [GATEWAY] MÉTODO RUTA → CÓDIGO (TIEMPOs)
        print(f"[GATEWAY] {request.method} {request.url.path} → {response.status_code} ({transcurrido}s)")
        
        return response


def validar_carga(archivo: UploadFile):
    if not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Solo se aceptan archivos PDF."
        )
    if archivo.size and archivo.size > TAM_MAX_ARCHIVOS_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {TAM_MAX_ARCHIVOS_MB} MB."
        )
