"""
Nodo Worker — API de Procesamiento
====================================
ESTADO:
  ✅ POST /process      — extracción + clasificación
  ✅ Heartbeat + Elección de Líder — election.py
  🔲 POST /delete-files — PENDIENTE FASE 5 (borrado en 2 pasos)
  🔲 Startup Sync       — PENDIENTE FASE 6
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import shutil, os, json

from .extractor import extraer_texto
from .classifier import clasificar
from shared.election import iniciar as iniciar_eleccion, yo_soy_lider, obtener_url_lider
from master.routes import router as router_maestro

app = FastAPI()

RUTA_TEMP = "temp.pdf"
# TODO FASE 7: hacer configurable por variable de entorno o argumento CLI
ALMACENAMIENTO_NODO = os.getenv("ALMACENAMIENTO_NODO", "../storage/node1")


# ── Middleware de redirección al líder ───────────────────────────────────────
# Endpoints que este nodo siempre atiende sin importar si es líder o no
ENDPOINTS_LOCALES = {
    "/heartbeat",
    "/election/start",
    "/election/coordinator",
    "/leader",
    "/process",
    "/delete-files",
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
            {"detail": "Sin líder disponible. Reintenta en unos segundos."},
            status_code=503,
        )

app.add_middleware(RedirigirAlLiderMiddleware)


# ── Rutas del maestro (activas solo cuando este nodo es líder) ───────────────
app.include_router(router_maestro)


# ── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def evento_inicio():
    # Unirse al clúster y arrancar heartbeat
    iniciar_eleccion(app)

    # TODO FASE 6: descomentar cuando sync.py esté implementado.
    # from sync import ejecutar_sincronizacion_inicio
    # await ejecutar_sincronizacion_inicio()
    print("[WORKER] Iniciado. (Startup Sync pendiente — Fase 6)")


# ── ✅ IMPLEMENTADO ───────────────────────────────────────────────────────────

@app.post("/process")
async def procesar_archivo(
    archivo: UploadFile = File(...),
    areas_usuario: str  = Form(...)
):
    """✅ Extrae texto del PDF y clasifica con TF-IDF + LogisticRegression."""
    areas = json.loads(areas_usuario)

    with open(RUTA_TEMP, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    texto = extraer_texto(RUTA_TEMP)
    area  = clasificar(texto, areas)

    os.remove(RUTA_TEMP)
    return {"area": area}


# ── 🔲 PENDIENTE FASE 5 ───────────────────────────────────────────────────────

@app.post("/delete-files")
async def eliminar_archivos(archivos: list[dict]):
    """
    🔲 TODO FASE 5 — Borrado físico coordinado por el Maestro.

    Body esperado:
    [
      {"nombre_usuario": "erick", "area": "Redes", "subarea": "Protocolos", "nombre": "paper.pdf"},
      {"nombre_usuario": "erick", "area": "Redes", "subarea": "",            "nombre": "otro.pdf"}
    ]

    Pasos a implementar:
      1. Iterar la lista
      2. Construir ruta: ALMACENAMIENTO_NODO/{nombre_usuario}/{area}/{subarea}/{nombre}
      3. Eliminar si existe, registrar si no se encontró
      4. Retornar {"eliminados": [...], "no_encontrados": [...]}
    """
    raise HTTPException(status_code=501, detail="Pendiente implementación Fase 5.")