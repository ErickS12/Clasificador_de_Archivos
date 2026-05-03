"""
Sincronización de Borrados Pendientes
======================================
Este módulo implementa el mecanismo de eventual consistency para el borrado distribuido.
Cuando un nodo worker se levanta, sincroniza los borrados pendientes desde Supabase.

FASE 6 (Startup Sync) — Estado: ✅ IMPLEMENTADO

Pasos:
  1. Al iniciar el worker, lee borrados_pendientes con estado='pendiente'
  2. Para cada entrada, intenta borrar el archivo del disco local
  3. Si éxito → marca como 'completado' en BD
  4. Si fallo → incrementa intentos_fallidos
  5. Si >3 intentos → marca como 'fallido' (alerta manual)

Este sistema garantiza que los archivos huérfanos se limpian automáticamente
cuando los nodos se recuperan, sin bloquear al usuario.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# Aquí iría la inicialización de Supabase (inyectada desde worker/main.py)
# db = get_db()  # Implementación inyectada

NOMBRE_NODO = os.getenv("WORKER_NODE_NAME", "node1")  # 'node1', 'node2', 'node3', etc.
ALMACENAMIENTO_NODO = os.getenv("ALMACENAMIENTO_NODO", "../storage/node1")


def obtener_db():
    """
    Obtiene la instancia de Supabase.
    Implementación inyectada desde worker/main.py para evitar imports circulares.
    """
    from master.database import db
    return db


async def sincronizar_borrados_pendientes(db=None) -> dict:
    """
    Sincroniza los borrados pendientes para ESTE nodo al startup.
    
    Flujo:
      1. Lee todas las entradas de borrados_pendientes donde:
         - estado = 'pendiente'
         - nodo_destino = NOMBRE_NODO (p.ej. 'node1')
      2. Para cada una, intenta borrar el archivo del disco
      3. Marca como 'completado' si éxito, o incrementa intentos_fallidos
      4. Si intentos_fallidos > 3, marca como 'fallido'
    
    Retorna:
        dict con resultados: {
            "completados": [...],
            "fallidos": [...],
            "reintentos": [...],
            "timestamp": "2026-05-02T10:30:45Z"
        }
    """
    if db is None:
        db = obtener_db()
    
    resultados = {
        "completados": [],
        "fallidos": [],
        "reintentos": [],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    try:
        # Leer todas las entradas pendientes para este nodo
        resp = (
            db.table("borrados_pendientes")
            .select("id, documento_id, lista_archivos, intentos_fallidos")
            .eq("estado", "pendiente")
            .eq("nodo_destino", NOMBRE_NODO)
            .execute()
        )
        
        pendientes = resp.data or []
        print(f"[SYNC] {len(pendientes)} borrados pendientes para {NOMBRE_NODO}")
        
        for entrada in pendientes:
            id_borrado = entrada["id"]
            lista_archivos = entrada.get("lista_archivos", [])
            intentos = entrada.get("intentos_fallidos", 0)
            
            if intentos > 3:
                # Ya no reintentar, marcar como fallido
                db.table("borrados_pendientes").update({
                    "estado": "fallido",
                    "actualizado_en": datetime.utcnow().isoformat(),
                }).eq("id", id_borrado).execute()
                
                resultados["fallidos"].append({
                    "id": id_borrado,
                    "razon": "max_intentos_excedido"
                })
                continue
            
            # Intentar borrar todos los archivos de esta entrada
            todos_borrados = True
            errores = []
            
            for archivo in lista_archivos:
                nombre_usuario = archivo.get("nombre_usuario", "")
                area = archivo.get("area", "")
                subarea = archivo.get("subarea", "") or ""
                nombre = archivo.get("nombre", "")
                
                ruta = os.path.join(
                    ALMACENAMIENTO_NODO,
                    nombre_usuario,
                    area,
                    subarea,
                    nombre
                )
                
                try:
                    if os.path.exists(ruta):
                        os.remove(ruta)
                        print(f"[SYNC] ✓ Borrado: {ruta}")
                    else:
                        # Si el archivo ya no existe, está "borrado"
                        print(f"[SYNC] ⊘ No encontrado (ya limpio): {ruta}")
                except Exception as exc:
                    todos_borrados = False
                    errores.append(str(exc))
                    print(f"[SYNC] ✗ Error borrar {ruta}: {exc}")
            
            # Actualizar estado en BD
            if todos_borrados:
                # Éxito: marcar como completado
                db.table("borrados_pendientes").update({
                    "estado": "completado",
                    "actualizado_en": datetime.utcnow().isoformat(),
                }).eq("id", id_borrado).execute()
                
                resultados["completados"].append(id_borrado)
                print(f"[SYNC] ✓ Entrada {id_borrado} completada")
            else:
                # Fallo: incrementar intentos y reintentaremos después
                nuevo_intento = intentos + 1
                db.table("borrados_pendientes").update({
                    "intentos_fallidos": nuevo_intento,
                    "ultimo_intento": datetime.utcnow().isoformat(),
                    "actualizado_en": datetime.utcnow().isoformat(),
                }).eq("id", id_borrado).execute()
                
                resultados["reintentos"].append({
                    "id": id_borrado,
                    "intentos": nuevo_intento,
                    "errores": errores
                })
                print(f"[SYNC] ⟳ Entrada {id_borrado} reintentar (intento {nuevo_intento})")
        
        print(f"[SYNC] Resumen: {len(resultados['completados'])} ✓, "
              f"{len(resultados['reintentos'])} ⟳, {len(resultados['fallidos'])} ✗")
        
    except Exception as exc:
        print(f"[SYNC] Error crítico: {exc}")
        resultados["error"] = str(exc)
    
    return resultados


async def reintentar_borrados_periodicos(db=None, intervalo_segundos: int = 300):
    """
    Job periódico que intenta completar los borrados pendientes cada X segundos.
    
    Se ejecuta continuamente en background durante la vida del worker.
    Si hay reintentos fallidos, los intenta de nuevo sin bloquear otras operaciones.
    
    Args:
        db: Instancia de Supabase (opcional, se inyecta)
        intervalo_segundos: Cada cuánto reintentar (default: 5 minutos)
    """
    if db is None:
        db = obtener_db()
    
    print(f"[REINTENTOS] Iniciado - reintentaré cada {intervalo_segundos}s")
    
    while True:
        try:
            await asyncio.sleep(intervalo_segundos)
            resultado = await sincronizar_borrados_pendientes(db)
            
            if resultado.get("reintentos"):
                print(f"[REINTENTOS] {len(resultado['reintentos'])} entradas reintentar")
            
        except Exception as exc:
            print(f"[REINTENTOS] Error: {exc}")


# ── Funciones helper para testing ────────────────────────────────────────────

def obtener_borrados_pendientes_para_nodo(nodo: str, db=None) -> list[dict]:
    """Obtiene todas las entradas pendientes para un nodo específico."""
    if db is None:
        db = obtener_db()
    
    resp = (
        db.table("borrados_pendientes")
        .select("*")
        .eq("nodo_destino", nodo)
        .eq("estado", "pendiente")
        .execute()
    )
    return resp.data or []


def limpiar_borrados_completados(dias: int = 7, db=None) -> int:
    """
    Limpia registros 'completados' más antiguos que X días.
    Evita que la tabla crezca demasiado.
    """
    if db is None:
        db = obtener_db()
    
    fecha_limite = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    
    resp = (
        db.table("borrados_pendientes")
        .delete()
        .eq("estado", "completado")
        .lt("actualizado_en", fecha_limite)
        .execute()
    )
    
    # Supabase devuelve count en response
    return len(resp.data or [])
