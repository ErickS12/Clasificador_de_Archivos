"""
Base de Datos — Tabla lider_actual
=====================================
Funciones de Supabase para leer y escribir el líder activo del clúster.

"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno del archivo .env
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def obtener_lider_actual() -> dict | None:
    """
    Retorna el líder registrado en Supabase.

    Retorna dict con {"nodo_id", "nodo_url", "ultimo_heartbeat"}
    o None si no hay líder registrado aún.
    """
    try:
        res = db.table("lider_actual").select("*").eq("id", 1).execute()
        if res.data and res.data[0]["nodo_id"] != 0:
            return res.data[0]
        return None
    except Exception as e:
        print(f"[LEADER_DB] Error al leer líder: {e}")
        return None


def guardar_lider(datos: dict):
    """
    Guarda (upsert) el nuevo líder en Supabase.

    Parámetros:
        datos — {"nodo_id": int, "nodo_hostname": str, "nodo_url": str}
    """
    try:
        hostname = datos.get("nodo_hostname", f"nodo{datos['nodo_id']}")
        db.table("lider_actual").upsert({
            "id":             1,
            "nodo_id":        datos["nodo_id"],
            "nodo_hostname":  hostname,
            "nodo_url":       datos["nodo_url"],
        }).execute()
        print(f"[LEADER_DB] Líder guardado: Nodo {datos['nodo_id']} ({hostname})") 
    except Exception as e:
        print(f"[LEADER_DB] Error al guardar líder: {e}")


def actualizar_heartbeat(nodo_id: int):
    """
    El líder actual actualiza su timestamp de heartbeat.
    Llamar periódicamente desde election.py para que los demás
    puedan detectar si el líder dejó de responder.
    """
    try:
        db.table("lider_actual").update({
            "ultimo_heartbeat": "now()",
        }).eq("id", 1).eq("nodo_id", nodo_id).execute()
    except Exception as e:
        print(f"[LEADER_DB] Error al actualizar heartbeat: {e}")
