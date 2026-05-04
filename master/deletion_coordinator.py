"""
Coordinador de Borrado Distribuido con Eventual Consistency
═════════════════════════════════════════════════════════════
ESTADO: ✅ IMPLEMENTADO — FASE 5 + FASE 6

Implementa el patrón "Consistencia Eventual" para garantizar que los archivos
nunca quedan huérfanos, incluso si algunos nodos se caen durante el borrado.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLUJO DEL BORRADO (3 pasos):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASO 1 — BORRADO FÍSICO (workers):
  1. El Maestro obtiene lista de PDFs del documento
  2. Envía POST /delete-files a TODOS los workers (2+ de 3 = éxito)
  3. Los workers responden con confirmación
  4. Si alguno falla → registra en tabla 'borrados_pendientes' para reintento

PASO 2 — BORRADO LÓGICO (Supabase):
  5. SI al menos 2 de 3 workers confirmaron OK → borra en Supabase
  6. Para los nodos que fallaron, crea registro en 'borrados_pendientes'
  7. Usuario ve "eliminado" (ilusión de inmediatez)
  8. ON DELETE CASCADE limpia automáticamente en BD

PASO 3 — SINCRONIZACIÓN EVENTUAL (worker startup):
  9. Cuando un nodo caído se levanta, ejecuta sync.py
  10. Busca en 'borrados_pendientes' para SU nodo
  11. Limpia automáticamente los archivos zombies
  12. Marca registro como 'completado'

GARANTÍAS:
  ✓ Usuario nunca se bloquea (2+ exitosos = success)
  ✓ Archivos huérfanos se limpian al startup del nodo
  ✓ Sin bloqueos en cascada (eventual consistency)
  ✓ Job periódico reintenta fallidos c/5min
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import requests
from datetime import datetime
from fastapi import HTTPException

from master.database import db, obtener_nodos_documento, obtener_usuario_por_nombre
from shared.cluster_config import obtener_nodos_cluster

WORKER_URLS = [nodo["url"] for nodo in obtener_nodos_cluster() if int(nodo["id"]) != 4]

NODOS = ["node1", "node2", "node3"]
MIN_WORKERS_EXITOSOS = 2  # Al menos 2 de 3 deben ser exitosos


def solicitar_borrado_fisico(lista_archivos: list[dict]) -> tuple[dict[str, bool], list[str]]:
    """
    Intenta borrar archivos en todos los workers.
    
    NUEVO PATRÓN: 2+ de 3 = ÉXITO (partial success)
    Los nodos que fallan se registran en borrados_pendientes para reintento.
    
    Parámetros:
        lista_archivos — lista de dicts con {"nombre", "area", "subarea", "nombre_usuario"}

    Retorna:
        (dict[str, bool], list[str]):
            - dict: {"node1": True, "node2": False, ...}
            - list: nodos que fallaron (para crear registros de pendientes)
    """
    resultados: dict[str, bool] = {}
    nodos_fallidos: list[str] = []

    for i, url in enumerate(WORKER_URLS):
        nodo = f"node{i + 1}"
        exito = False
        ultimo_error = None

        # Reintentar hasta 3 veces por nodo
        for intento in range(3):
            try:
                response = requests.post(f"{url}/delete-files", json=lista_archivos, timeout=15)
                if response.status_code in (200, 207):
                    payload = response.json() if response.content else {}
                    errores = payload.get("errores", []) if isinstance(payload, dict) else []
                    if not errores:
                        exito = True
                        break
                    ultimo_error = f"errores en respuesta: {errores}"
                else:
                    ultimo_error = f"status {response.status_code}"
            except Exception as exc:
                ultimo_error = str(exc)

        if not exito:
            nodos_fallidos.append(nodo)
            print(f"[DELETE] Error en {nodo}: {ultimo_error}")
        else:
            print(f"[DELETE] ✓ {nodo} borró exitosamente")

        resultados[nodo] = exito

    return resultados, nodos_fallidos


def registrar_borrados_pendientes(
    documento_id: str,
    nodos_fallidos: list[str],
    lista_archivos: list[dict]
) -> list[str]:
    """
    Crea registros en 'borrados_pendientes' para los nodos que fallaron.
    
    Cuando estos nodos se levanten, ejecutarán sync.py y limpiarán automáticamente.
    
    Parámetros:
        documento_id: UUID del documento (FK a borrados_pendientes)
        nodos_fallidos: ['node1', 'node2'] etc
        lista_archivos: la misma lista que se intentó borrar
    
    Retorna:
        lista de IDs creados (para logging)
    """
    ids_creados = []
    
    for nodo in nodos_fallidos:
        try:
            resp = db.table("borrados_pendientes").insert({
                "documento_id": documento_id,
                "nodo_destino": nodo,
                "lista_archivos": lista_archivos,
                "estado": "pendiente",
                "intentos_fallidos": 0,
                "creado_en": datetime.utcnow().isoformat(),
                "actualizado_en": datetime.utcnow().isoformat(),
            }).execute()
            
            if resp.data:
                id_pendiente = resp.data[0]["id"]
                ids_creados.append(id_pendiente)
                print(f"[PENDIENTES] Creado registro para {nodo}: {id_pendiente}")
        except Exception as exc:
            print(f"[PENDIENTES] Error creando registro: {exc}")
    
    return ids_creados


def confirmar_y_purgar_base_datos(
    documento_id: str,
    resultados_nodo: dict[str, bool],
    nodos_fallidos: list[str],
    lista_archivos: list[dict]
) -> dict:
    """
    NUEVO PATRÓN: Eventual Consistency
    
    Si 2+ workers confirmaron OK → borra en Supabase AHORA
    Para los que fallaron → registra en borrados_pendientes (se sync después)
    
    Retorna:
        dict con resumen de lo que pasó
    """
    exitosos = sum(1 for v in resultados_nodo.values() if v)
    
    # Chequear si al menos MIN_WORKERS_EXITOSOS tuvieron éxito
    if exitosos < MIN_WORKERS_EXITOSOS:
        fallidos_str = [n for n, ok in resultados_nodo.items() if not ok]
        raise HTTPException(
            status_code=503,
            detail=f"Insuficientes workers exitosos ({exitosos}/{len(NODOS)}). Fallaron: {fallidos_str}",
        )

    # ÉXITO: Al menos 2 de 3 funcionaron
    # Borra en Supabase AHORA (ilusión de inmediatez para el usuario)
    db.table("documentos").delete().eq("id", documento_id).execute()
    print(f"[DELETE] ✓ Borrado en Supabase (documento_id={documento_id})")

    # Registra pendientes para los que fallaron (se van a sincronizar después)
    ids_pendientes = []
    if nodos_fallidos:
        ids_pendientes = registrar_borrados_pendientes(documento_id, nodos_fallidos, lista_archivos)

    return {
        "exitosos": exitosos,
        "fallidos": len(nodos_fallidos),
        "pendientes_creados": len(ids_pendientes),
        "ids_pendientes": ids_pendientes,
    }


async def eliminar_tema_con_archivos(documento_id: str, nombre_usuario: str):
    """
    Punto de entrada principal del borrado distribuido.
    Implementa eventual consistency (OPCIÓN A).
    
    Flujo:
        1. Obtener info del documento desde Supabase
        2. Enviar POST /delete-files a todos los workers
        3. Si 2+ exitosos → borra en Supabase AHORA (user ve "eliminado")
        4. Para los que fallaron → crea registros en borrados_pendientes
        5. Cuando el nodo caído se levante, sync.py limpia automáticamente
    
    Retorna:
        {
            "mensaje": "...",
            "nodos": {"node1": True, "node2": False, ...},
            "pendientes": ["id1", "id2"],  # registros creados
            "estado": "éxito_total" | "éxito_parcial" | "fallo"
        }
    """
    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    documento = (
        db.table("documentos")
        .select("id, nombre_archivo, tematica_id, subtematica_id")
        .eq("id", documento_id)
        .eq("usuario_id", usuario["id"])
        .single()
        .execute()
    )

    if not documento.data:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    doc = documento.data
    tematica = db.table("tematicas").select("nombre").eq("id", doc["tematica_id"]).single().execute().data
    if not tematica:
        raise HTTPException(status_code=404, detail="Tematica del documento no encontrada.")

    subarea = ""
    if doc.get("subtematica_id"):
        sub = db.table("subtematicas").select("nombre").eq("id", doc["subtematica_id"]).single().execute().data
        if sub:
            subarea = sub["nombre"]

    lista_archivos = [
        {
            "nombre_usuario": nombre_usuario,
            "area": tematica["nombre"],
            "subarea": subarea,
            "nombre": doc["nombre_archivo"],
        }
    ]

    # PASO 1: Intenta borrar en todos los workers
    resultados, nodos_fallidos = solicitar_borrado_fisico(lista_archivos)
    
    # PASO 2 + 3: Borra en Supabase si 2+ exitosos, registra pendientes si alguno falló
    try:
        resumen = confirmar_y_purgar_base_datos(
            doc["id"],
            resultados,
            nodos_fallidos,
            lista_archivos
        )
    except HTTPException as exc:
        # Menos de 2 exitosos → no se borra nada
        raise exc

    estado = "éxito_total" if not nodos_fallidos else "éxito_parcial"
    
    return {
        "mensaje": f"Documento eliminado (estado: {estado})",
        "nodos": resultados,
        "pendientes": resumen.get("ids_pendientes", []),
        "estado": estado,
        "resumen": resumen,
    }
