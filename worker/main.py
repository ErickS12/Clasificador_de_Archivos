"""
Nodo Worker — API de Procesamiento
====================================
ESTADO:
  ✅ POST /process      — extracción + clasificación
  ✅ Heartbeat + Elección de Líder — election.py
  ✅ POST /delete-files — borrado en 2 pasos
  ✅ Startup Sync       — sincronización de pendientes (eventual consistency)
"""

# Cargar variables de entorno ANTES de cualquier otra importación
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import shutil, os, json, asyncio

from .extractor import extraer_texto
from .classifier import clasificar
from shared.election import iniciar as iniciar_eleccion, yo_soy_lider, obtener_url_lider
from shared.sync import sincronizar_borrados_pendientes, reintentar_borrados_periodicos
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

    # FASE 6: Sincronización de borrados pendientes con patrón PUSH
    # Worker notifica al Master cuando se levanta
    asyncio.create_task(sincronizar_con_master_al_startup())
    
    print(f"[WORKER] Iniciado. Sincronizando borrados pendientes...")


async def sincronizar_con_master_al_startup():
    """
    Al startup, notifica al master y sincroniza inmediatamente los borrados pendientes.
    Patrón PUSH: Worker → Master (en lugar de Master → Worker cada 5 minutos)
    """
    import requests
    from shared.sync import sincronizar_borrados_pendientes
    
    # Esperar un poquito a que el worker esté listo
    await asyncio.sleep(1)
    
    try:
        # 1. Notificar al master: "Estoy vivo"
        url_master = os.getenv("MASTER_URL", "http://localhost:8000")
        resp = requests.post(
            f"{url_master}/node-startup",
            json={"node_name": os.getenv("WORKER_NODE_NAME", "node1")},
            timeout=5
        )
        
        respuesta = resp.json()
        borrados = respuesta.get("borrados_pendientes", [])
        
        # 2. Sincronizar inmediatamente con los datos del master
        if borrados:
            print(f"[STARTUP-SYNC] Master envió {len(borrados)} borrados pendientes")
            resultado = await sincronizar_borrados_pendientes(lista_previa=borrados)
            print(f"[STARTUP-SYNC] Resultado: {resultado['completados'].__len__()} completados, "
                  f"{resultado['fallidos'].__len__()} fallidos, "
                  f"{resultado['reintentos'].__len__()} reintentos")
        else:
            print(f"[STARTUP-SYNC] Sin borrados pendientes - sistema consistente")
    
    except requests.exceptions.Timeout:
        print(f"[STARTUP-SYNC] Master offline (timeout) - sincronizando fallback desde BD")
        # Fallback: sincronizar sin info del master (polling local)
        resultado = await sincronizar_borrados_pendientes()
        print(f"[STARTUP-SYNC] Fallback: {resultado}")
    
    except Exception as e:
        print(f"[STARTUP-SYNC] Error contactando master: {e} - sincronizando fallback")
        # Fallback: sincronizar sin info del master
        resultado = await sincronizar_borrados_pendientes()
        print(f"[STARTUP-SYNC] Fallback: {resultado}")


# ── ✅ IMPLEMENTADO ───────────────────────────────────────────────────────────

@app.post("/process")
async def procesar_archivo(
    archivo: UploadFile = File(...),
    categorias_global: str  = Form(...)
):
    """✅ Extrae texto del PDF y clasifica usando modelo jerárquico.
    
    Recibe:
        archivo - PDF a clasificar
        categorias_global - JSON con lista de todas las categorías disponibles
                           Ej: ["Tecnología/Inteligencia Artificial", "Tecnología/Redes", ...]
    
    Devuelve:
        {"area": "Tecnología/Inteligencia Artificial"}
    """
    categorias = json.loads(categorias_global)

    with open(RUTA_TEMP, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    texto = extraer_texto(RUTA_TEMP)
    area = clasificar(texto, categorias)

    os.remove(RUTA_TEMP)
    return {"area": area}


# ── ✅ FASE 5: Borrado en 2 pasos ───────────────────────────────────────────

@app.post("/delete-files")
async def eliminar_archivos(archivos: list[dict] = Body(...)):
    """
    Borra archivos físicos en este nodo.

    Body esperado:
    [
      {"nombre_usuario": "erick", "area": "Redes", "subarea": "Protocolos", "nombre": "paper.pdf"},
      {"nombre_usuario": "erick", "area": "Redes", "subarea": "",            "nombre": "otro.pdf"}
    ]

    Retorna:
      {"eliminados": [...], "no_encontrados": [...], "errores": [...]} 
    """
    eliminados: list[str] = []
    no_encontrados: list[str] = []
    errores: list[str] = []

    for archivo in archivos:
        nombre_usuario = archivo.get("nombre_usuario", "")
        area = archivo.get("area", "")
        subarea = archivo.get("subarea", "") or ""
        nombre = archivo.get("nombre", "")

        if not nombre_usuario or not area or not nombre:
            errores.append(f"Registro invalido: {archivo}")
            continue

        ruta = os.path.join(ALMACENAMIENTO_NODO, nombre_usuario, area, subarea, nombre)
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
                eliminados.append(ruta)
            except Exception as exc:
                errores.append(f"No se pudo borrar {ruta}: {exc}")
        else:
            no_encontrados.append(ruta)

    status_code = 200 if not errores else 207
    return JSONResponse(status_code=status_code, content={
        "eliminados": eliminados,
        "no_encontrados": no_encontrados,
        "errores": errores,
    })


# ── ✅ FASE 6: Sincronización de borrados pendientes (startup) ────────────────

@app.on_event("startup")
async def sincronizar_al_iniciar():
    """
    Evento de startup: sincroniza los borrados pendientes de este nodo.
    
    Cuando el nodo se levanta, compara los archivos pendientes en la BD
    con los archivos en su almacenamiento local y limpia los huérfanos.
    """
    print("[STARTUP] Iniciando sincronización de borrados pendientes...")
    try:
        resultado = await sincronizar_borrados_pendientes()
        print(f"[STARTUP] Sincronización completada: {resultado}")
    except Exception as exc:
        print(f"[STARTUP] ⚠️ Error en sincronización: {exc}")


@app.on_event("startup")
async def iniciar_reintentos_periodicos():
    """
    Evento de startup: inicia un job periódico que reintenta borrados fallidos.
    
    Corre en background cada 5 minutos, intenta completar los borrados
    que fallaron anteriormente.
    """
    print("[STARTUP] Iniciando job periódico de reintentos...")
    asyncio.create_task(reintentar_borrados_periodicos(intervalo_segundos=300))