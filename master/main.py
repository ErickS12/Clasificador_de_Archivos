"""
Nodo Maestro - API principal.
La logica de negocio vive en master/routes.py y persiste en Supabase.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from shared.election import iniciar as iniciar_eleccion, yo_soy_lider, obtener_url_lider
from .gateway import LoggingMiddleware
from .routes import router

app = FastAPI(title="Clasificador Distribuido de Archivos Cientificos")

ENDPOINTS_LOCALES = {
    "/heartbeat",
    "/election/start",
    "/election/coordinator",
    "/leader",
    "/docs",
    "/openapi.json",
}


class RedirigirAlLiderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ENDPOINTS_LOCALES or yo_soy_lider():
            return await call_next(request)

        url_lider = obtener_url_lider()
        if url_lider:
            destino = f"{url_lider}{request.url.path}"
            if request.url.query:
                destino += f"?{request.url.query}"
            return RedirectResponse(url=destino, status_code=307)

        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"detail": "Sin lider disponible. Reintenta en unos segundos."},
            status_code=503,
        )


app.add_middleware(RedirigirAlLiderMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(router)


@app.on_event("startup")
async def evento_inicio():
    iniciar_eleccion(app)
    print("[MASTER] Iniciado.")
