"""
Startup Sync — Sincronización de Recuperación al Inicio
=========================================================
ESTADO: 🔲 PENDIENTE — FASE 6

Se activa automáticamente cuando un worker arranca (startup event de FastAPI).
Compara el inventario local del nodo contra Supabase y descarga los archivos
faltantes para restaurar la consistencia tras una caída.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLUJO DE SINCRONIZACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Al iniciar el worker:
  1. Consultar Supabase → lista de TODOS los documentos que debería tener
  2. Escanear la carpeta local (ej. storage/node2/) → inventario real
  3. Comparar ambas listas:
     - Archivo en Supabase pero NO en local → DESCARGAR desde el maestro
     - Archivo en local pero NO en Supabase → ELIMINAR del disco (huérfano)
  4. Registrar en consola el resultado de la sincronización

Endpoint necesario en master/main.py:
  GET /internal/file?filename=&area=&subarea=&username=
  → Solo accesible desde workers (no expuesto al cliente web)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import requests

# TODO FASE 7: reemplazar con IP real del maestro en la LAN
URL_MAESTRO = "http://localhost:8000"

# Carpeta local de este nodo (cambiar según el número de nodo)
# node1 → storage/node1, node2 → storage/node2, etc.
ALMACENAMIENTO_NODO = "../storage/node1"  # TODO: hacer configurable por variable de entorno


def obtener_archivos_esperados_de_bd() -> list[dict]:
    """
    TODO FASE 6: Consultar Supabase y obtener la lista completa
    de documentos que este nodo debería tener almacenados.

    Retorna lista de dicts:
    [{"nombre": "paper.pdf", "nombre_usuario": "erick", "area": "Redes", "subarea": "Protocolos"}, ...]
    """
    # TODO FASE 6: implementar con cliente Supabase
    raise NotImplementedError("Implementar en Fase 6.")


def obtener_inventario_local() -> set[str]:
    """
    Escanea la carpeta local del nodo y devuelve un set de rutas relativas.
    Ejemplo: {"erick/Redes/Protocolos/paper.pdf", "juan/General/doc.pdf"}
    """
    inventario = set()
    for root, _, files in os.walk(ALMACENAMIENTO_NODO):
        for filename in files:
            full_path = os.path.join(root, filename)
            relativa  = os.path.relpath(full_path, ALMACENAMIENTO_NODO)
            inventario.add(relativa)
    return inventario


def descargar_archivo_faltante(nombre_usuario: str, area: str, subarea: str, nombre_archivo: str):
    """
    TODO FASE 6: Descargar un archivo faltante desde el maestro.
    Usar el endpoint interno GET /internal/file del maestro.
    """
    # TODO FASE 6: implementar
    raise NotImplementedError("Implementar en Fase 6.")


def eliminar_archivo_huerfano(ruta_relativa: str):
    """
    Elimina un archivo local que ya no existe en Supabase (huérfano).
    """
    ruta_completa = os.path.join(ALMACENAMIENTO_NODO, ruta_relativa)
    if os.path.exists(ruta_completa):
        os.remove(ruta_completa)
        print(f"[SYNC] Huérfano eliminado: {ruta_relativa}")


async def ejecutar_sincronizacion_inicio():
    """
    TODO FASE 6: Punto de entrada principal del Startup Sync.
    Llamar desde el evento @app.on_event("startup") en worker/main.py.

    Implementación pendiente:
        1. esperados = obtener_archivos_esperados_de_bd()
        2. local    = obtener_inventario_local()
        3. Para cada archivo esperado no en local → descargar_archivo_faltante()
        4. Para cada archivo local no en esperados → eliminar_archivo_huerfano()
        5. Imprimir resumen en consola
    """
    print("[SYNC] Iniciando sincronización de recuperación...")
    # TODO FASE 6: implementar
    print("[SYNC] (pendiente implementación Fase 6)")
