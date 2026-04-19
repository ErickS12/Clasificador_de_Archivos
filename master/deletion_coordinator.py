"""
Coordinador de Borrado en Dos Pasos
=====================================
ESTADO: 🔲 PENDIENTE — FASE 5

Garantiza la consistencia entre el almacenamiento físico (nodos)
y el registro lógico (Supabase) al eliminar temáticas con documentos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLUJO DEL BORRADO EN 2 PASOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASO 1 — Borrado FÍSICO (workers):
  1. El Maestro consulta Supabase → lista de PDFs de la temática
  2. Envía POST /delete-files a cada worker con la lista de archivos
  3. Cada worker elimina los PDFs de su carpeta local (node1/2/3)
  4. Los workers responden con confirmación

PASO 2 — Borrado LÓGICO (Supabase):
  5. Solo si el Paso 1 fue exitoso en todos los nodos disponibles
  6. El Maestro llama DELETE /themes/{id} en Supabase
  7. ON DELETE CASCADE elimina subtemáticas y registros de documentos

Si el Paso 1 falla (algún worker no responde):
  → Se registra el error, NO se procede con el Paso 2
  → El administrador debe reintentar o resolver manualmente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import requests
from fastapi import HTTPException

# IPs de workers (misma lista que consensus.py)
# TODO FASE 7: reemplazar con IPs reales de la LAN
WORKER_URLS = [
    "http://localhost:5001",
    "http://localhost:5002",
    "http://localhost:5003",
]


def solicitar_borrado_fisico(lista_archivos: list[dict]) -> dict[str, bool]:
    """
    TODO FASE 5: Enviar la lista de archivos a eliminar a cada worker.

    Parámetros:
        lista_archivos — lista de dicts con {"nombre", "area", "subarea", "nombre_usuario"}

    Retorna:
        dict con resultado por nodo: {"node1": True, "node2": False, ...}

    Implementación pendiente:
        - Agregar endpoint POST /delete-files en worker/main.py
        - Cada worker itera la lista y elimina los archivos de su carpeta
        - Retorna 200 si todo OK, 207 si hubo errores parciales
    """
    # TODO FASE 5: implementar
    raise NotImplementedError("Implementar en Fase 5.")


def confirmar_y_purgar_base_datos(id_tema: str, resultados_nodo: dict[str, bool]):
    """
    TODO FASE 5: Solo si todos los nodos disponibles confirmaron el borrado,
    proceder con el DELETE en Supabase (ON DELETE CASCADE).

    Si algún nodo falló, lanzar excepción y NO borrar en Supabase.
    """
    # TODO FASE 5: implementar
    raise NotImplementedError("Implementar en Fase 5.")


async def eliminar_tema_con_archivos(id_tema: str, nombre_usuario: str):
    """
    TODO FASE 5: Punto de entrada principal del borrado en 2 pasos.
    Llamar desde el endpoint DELETE /themes/{id} cuando el rol es admin.

    Flujo:
        1. Obtener lista de documentos de la temática desde Supabase
        2. solicitar_borrado_fisico(lista_archivos)
        3. confirmar_y_purgar_base_datos(id_tema, resultados)
        4. Retornar confirmación al admin
    """
    # TODO FASE 5: implementar
    raise NotImplementedError("Implementar en Fase 5.")
