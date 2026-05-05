"""
Nodo Maestro - API principal.
La logica de negocio vive en master/routes.py y persiste en Supabase.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from shared.election import iniciar as iniciar_eleccion, yo_soy_lider, obtener_url_lider
from master.database import (
    obtener_solicitudes_borrado_pendientes,
    actualizar_solicitud_borrado,
)
from master.deletion_coordinator import eliminar_tema_con_archivos
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


async def procesar_cola_borrados():
    """Procesa en background las solicitudes de borrado aceptadas."""
    while True:
        try:
            solicitudes = obtener_solicitudes_borrado_pendientes(limite=10)
            if not solicitudes:
                await asyncio.sleep(5)
                continue

            for solicitud in solicitudes:
                cola_id = solicitud["id"]
                documento_id = solicitud["documento_id"]
                nombre_usuario = solicitud.get("nombre_usuario") or solicitud["usuario_id"]

                try:
                    resultado = await eliminar_tema_con_archivos(documento_id, nombre_usuario)
                    actualizar_solicitud_borrado(
                        cola_id,
                        estado="completado",
                        actualizado_en="now()",
                    )
                    print(f"[QUEUE] Solicitud {cola_id} completada")
                except Exception as exc:
                    actualizar_solicitud_borrado(
                        cola_id,
                        estado="pendiente",
                        intentos=(solicitud.get("intentos") or 0) + 1,
                        ultimo_error=str(exc),
                        actualizado_en="now()",
                    )
                    print(f"[QUEUE] Solicitud {cola_id} reintentable: {exc}")

        except Exception as exc:
            print(f"[QUEUE] Error procesando cola: {exc}")

        await asyncio.sleep(5)


@app.on_event("startup")
async def evento_inicio():
    iniciar_eleccion(app)
    asyncio.create_task(procesar_cola_borrados())
    print("[MASTER] Iniciado.")
