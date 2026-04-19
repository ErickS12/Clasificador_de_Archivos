"""
Nodo Worker — API de Procesamiento
====================================
ESTADO:
  ✅ POST /process      — extracción + clasificación
  🔲 POST /delete-files — PENDIENTE FASE 5 (borrado en 2 pasos)
  🔲 Startup Sync       — PENDIENTE FASE 6
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import shutil, os, json
from extractor import extraer_texto
from classifier import clasificar

app = FastAPI()

RUTA_TEMP    = "temp.pdf"
# TODO FASE 7: hacer configurable por variable de entorno o argumento CLI
# node1 = storage/node1, node2 = storage/node2, node3 = storage/node3
ALMACENAMIENTO_NODO = "../storage/node1"


# ── FASE 6: hook de sincronización al arrancar ───────────────────
@app.on_event("startup")
async def evento_inicio():
    """
    TODO FASE 6: descomentar cuando sync.py esté implementado.

    from sync import ejecutar_sincronizacion_inicio
    await ejecutar_sincronizacion_inicio()
    """
    print("[WORKER] Iniciado. (Startup Sync pendiente — Fase 6)")


# ── ✅ IMPLEMENTADO ───────────────────────────────────────────────

@app.post("/process")
async def procesar_archivo(
    archivo: UploadFile = File(...),
    áreas_usuario: str  = Form(...)
):
    """✅ Extrae texto del PDF y clasifica con TF-IDF + LogisticRegression."""
    áreas = json.loads(áreas_usuario)

    with open(RUTA_TEMP, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    texto = extraer_texto(RUTA_TEMP)
    area = clasificar(texto, áreas)

    os.remove(RUTA_TEMP)
    return {"area": area}


# ── 🔲 PENDIENTE FASE 5 ───────────────────────────────────────────

@app.post("/delete-files")
async def eliminar_archivos(archivos: list[dict]):
    """
    🔲 TODO FASE 5 — Borrado físico coordinado por el Maestro.

    Recibe lista de archivos y los elimina de la carpeta local de este nodo.

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
