"""
Gestor de Base de Datos - Supabase / PostgreSQL
================================================
ESTADO: IMPLEMENTACION FASE 4

Este modulo gestiona la persistencia en Supabase.
Proporciona funciones para:
- Autenticacion y tokens
- Jerarquia de documentos (tematicas + subtematicas)
- Replicacion distribuida (nodos de almacenamiento)
- Registro de consenso de clasificacion
- Liderazgo del cluster
"""

from supabase import create_client, Client
import os
from typing import Optional, List, Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── USUARIOS ─────────────────────────────────────────────────────────────────


def obtener_usuario_por_nombre(nombre_usuario: str) -> Optional[Dict[str, Any]]:
    """Consultar usuario por nombre."""
    try:
        response = db.table("usuarios").select("*").eq("username", nombre_usuario).single().execute()
        return response.data if response.data else None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None


def obtener_usuario_por_id(usuario_id: str) -> Optional[Dict[str, Any]]:
    """Consultar usuario por UUID."""
    try:
        response = db.table("usuarios").select("*").eq("id", usuario_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None


def insertar_usuario(username: str, password_hash: str, rol_id: int = 2) -> Optional[str]:
    """
    Crear nuevo usuario.
    rol_id: 1 = admin, 2 = user (default)
    Retorna el UUID del usuario creado.
    """
    try:
        response = db.table("usuarios").insert({
            "username": username,
            "password_hash": password_hash,
            "rol_id": rol_id,
            "activo": True
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"Error insertando usuario: {e}")
        return None


def actualizar_usuario(usuario_id: str, **campos) -> bool:
    """Actualizar campos del usuario (nombre, contrasena, rol, activo)."""
    try:
        db.table("usuarios").update(campos).eq("id", usuario_id).execute()
        return True
    except Exception as e:
        print(f"Error actualizando usuario: {e}")
        return False


# ── TOKENS DE SESION ─────────────────────────────────────────────────────────


def crear_token_sesion(usuario_id: str, token_hash: str, expira_en: str) -> Optional[str]:
    """
    Crear token de sesion.
    expira_en: timestamp ISO 8601 (ej: '2026-04-23T12:00:00Z')
    Retorna el token_id.
    """
    try:
        response = db.table("tokens_sesion").insert({
            "usuario_id": usuario_id,
            "token_hash": token_hash,
            "expira_en": expira_en,
            "revocado": False
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"Error creando token: {e}")
        return None


def obtener_token(token_hash: str) -> Optional[Dict[str, Any]]:
    """Verificar si token existe, no esta revocado y no ha expirado."""
    try:
        response = db.table("tokens_sesion").select("*").eq("token_hash", token_hash).single().execute()
        token = response.data if response.data else None
        
        if token and not token["revocado"]:
            return token
        return None
    except Exception as e:
        print(f"Error obteniendo token: {e}")
        return None


def revocar_token(token_hash: str) -> bool:
    """Revocar un token de sesion."""
    try:
        db.table("tokens_sesion").update({"revocado": True}).eq("token_hash", token_hash).execute()
        return True
    except Exception as e:
        print(f"Error revocando token: {e}")
        return False


# ── TEMATICAS - CATALOGO GLOBAL DE SOLO LECTURA ──────────────────────────────


def obtener_catalogo_global() -> List[Dict[str, Any]]:
    """Obtener todas las temáticas del catálogo global."""
    try:
        response = db.table("tematicas").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error obteniendo catálogo global: {e}")
        return []


def obtener_categorias_globales() -> List[str]:
    """Obtener lista de todas las categorías jerárquicas disponibles.
    
    Retorna: ["Tecnología/Inteligencia Artificial", "Tecnología/Redes", ...]
    """
    try:
        # Obtener todas las tematicas
        tematicas = db.table("tematicas").select("id, nombre").execute()
        categorias = []
        
        if tematicas.data:
            for tematica in tematicas.data:
                tematica_id = tematica["id"]
                tematica_nombre = tematica["nombre"]
                
                # Obtener subtematicas de esta tematica
                subtematicas = db.table("subtematicas").select("nombre").eq("tematica_id", tematica_id).execute()
                
                if subtematicas.data:
                    for sub in subtematicas.data:
                        ruta = f"{tematica_nombre}/{sub['nombre']}"
                        categorias.append(ruta)
        
        return categorias
    except Exception as e:
        print(f"Error obteniendo categorías globales: {e}")
        return ["Otros/General"]  # Fallback


# ── SUBTEMATICAS - CATALOGO GLOBAL DE SOLO LECTURA ────────────────────────────


def obtener_subtematicas(tematica_id: str) -> List[Dict[str, Any]]:
    """Obtener todas las subtematicas de una tematica."""
    try:
        response = db.table("subtematicas").select("*").eq("tematica_id", tematica_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error obteniendo subtematicas: {e}")
        return []


def resolver_tema_predicho(ruta_predicha: str) -> tuple[Optional[str], Optional[str]]:
    """Resolver IDs de tematica y subtematica a partir de una ruta predicha.
    
    Args:
        ruta_predicha - ruta jerárquica (ej: "Tecnología/Inteligencia Artificial")
    
    Returns:
        (tematica_id, subtematica_id) o (None, None) si no existe
        
    Ejemplo:
        resolver_tema_predicho("Tecnología/Inteligencia Artificial") 
        -> ("uuid-tematica", "uuid-subtematica")
    """
    try:
        # Dividir la ruta
        partes = ruta_predicha.split("/")
        if len(partes) != 2:
            return None, None
        
        tematica_nombre, subtematica_nombre = partes
        
        # Buscar tematica
        res_tematica = db.table("tematicas").select("id").eq("nombre", tematica_nombre).single().execute()
        if not res_tematica.data:
            return None, None
        
        tematica_id = res_tematica.data["id"]
        
        # Buscar subtematica
        res_subtematica = db.table("subtematicas").select("id").eq("tematica_id", tematica_id).eq("nombre", subtematica_nombre).single().execute()
        if not res_subtematica.data:
            return None, None
        
        subtematica_id = res_subtematica.data["id"]
        return tematica_id, subtematica_id
        
    except Exception as e:
        print(f"Error resolviendo tema predicho: {e}")
        return None, None


# ── DOCUMENTOS ───────────────────────────────────────────────────────────────


def insertar_documento(
    usuario_id: str,
    tematica_id: str,
    nombre_archivo: str,
    hash_archivo: str,
    tamano_bytes: int,
    subtematica_id: Optional[str] = None
) -> Optional[str]:
    """
    Crear registro de documento.
    Retorna UUID del documento.
    """
    try:
        response = db.table("documentos").insert({
            "usuario_id": usuario_id,
            "tematica_id": tematica_id,
            "subtematica_id": subtematica_id,
            "nombre_archivo": nombre_archivo,
            "hash_original": hash_archivo,
            "tamano_bytes": tamano_bytes,
            "estado": "activo"
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"Error insertando documento: {e}")
        return None


def obtener_documentos_usuario(usuario_id: str) -> List[Dict[str, Any]]:
    """Obtener todos los documentos activos de un usuario."""
    try:
        response = db.table("documentos").select("*").eq("usuario_id", usuario_id).eq("estado", "activo").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error obteniendo documentos: {e}")
        return []


def actualizar_documento_clasificacion(
    documento_id: str,
    subtematica_id: str,
    confianza: float
) -> bool:
    """Registrar clasificacion final del documento."""
    try:
        db.table("documentos").update({
            "subtematica_id": subtematica_id,
            "confianza_clasificacion": confianza,
            "estado": "activo",
            "clasificado_en": "now()"
        }).eq("id", documento_id).execute()
        return True
    except Exception as e:
        print(f"Error actualizando documento: {e}")
        return False


def marcar_documento_eliminando(documento_id: str) -> bool:
    """Marcar documento en paso 1 de borrado (estado='eliminando')."""
    try:
        db.table("documentos").update({
            "estado": "eliminando",
            "eliminado_en": "now()"
        }).eq("id", documento_id).execute()
        return True
    except Exception as e:
        print(f"Error marcando documento como eliminando: {e}")
        return False


def marcar_documento_eliminado(documento_id: str) -> bool:
    """Marcar documento como completamente eliminado (paso 2)."""
    try:
        db.table("documentos").update({
            "estado": "eliminado"
        }).eq("id", documento_id).execute()
        return True
    except Exception as e:
        print(f"Error eliminando documento: {e}")
        return False


# ── CONSENSO DE VOTOS ────────────────────────────────────────────────────────


def insertar_voto_consenso(
    documento_id: str,
    nodo_worker: str,
    area_predicha: str,
    confianza_worker: float
) -> bool:
    """
    Registrar voto de un worker en la clasificacion.
    nodo_worker: 'node1', 'node2', 'node3'
    """
    try:
        db.table("consenso_votos").insert({
            "documento_id": documento_id,
            "nodo_worker": nodo_worker,
            "area_predicha": area_predicha,
            "confianza_worker": confianza_worker
        }).execute()
        return True
    except Exception as e:
        print(f"Error insertando voto: {e}")
        return False


def obtener_votos_documento(documento_id: str) -> List[Dict[str, Any]]:
    """Obtener todos los votos de una clasificacion."""
    try:
        response = db.table("consenso_votos").select("*").eq("documento_id", documento_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error obteniendo votos: {e}")
        return []


# ── NODOS DE ALMACENAMIENTO ──────────────────────────────────────────────────


def insertar_nodo_replicacion(
    documento_id: str,
    nodo: str,
    ruta_fisica: str
) -> bool:
    """
    Registrar que un documento fue replicado en un nodo.
    nodo: 'node1', 'node2', 'node3'
    """
    try:
        db.table("nodos_almacenamiento").insert({
            "documento_id": documento_id,
            "nodo": nodo,
            "ruta_fisica": ruta_fisica,
            "activo": True
        }).execute()
        return True
    except Exception as e:
        print(f"Error insertando nodo replicacion: {e}")
        return False


def obtener_nodos_documento(documento_id: str) -> List[Dict[str, Any]]:
    """Obtener en que nodos esta replicado un documento."""
    try:
        response = db.table("nodos_almacenamiento").select("*").eq("documento_id", documento_id).eq("activo", True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error obteniendo nodos: {e}")
        return []


def marcar_nodo_verificado(documento_id: str, nodo: str) -> bool:
    """Marcar un nodo como verificado (sync.py confirmo que existe el archivo)."""
    try:
        db.table("nodos_almacenamiento").update({
            "verificado_en": "now()"
        }).eq("documento_id", documento_id).eq("nodo", nodo).execute()
        return True
    except Exception as e:
        print(f"Error marcando nodo verificado: {e}")
        return False


def marcar_nodo_inactivo(documento_id: str, nodo: str) -> bool:
    """Marcar un nodo como inactivo (fallo en algun punto)."""
    try:
        db.table("nodos_almacenamiento").update({"activo": False}).eq("documento_id", documento_id).eq("nodo", nodo).execute()
        return True
    except Exception as e:
        print(f"Error marcando nodo inactivo: {e}")
        return False


# ── LIDERAZGO ────────────────────────────────────────────────────────────────


def actualizar_lider(nodo_id: int, nodo_hostname: str, nodo_url: str) -> bool:
    """Actualizar el nodo lider actual del cluster."""
    try:
        db.table("lider_actual").update({
            "nodo_id": nodo_id,
            "nodo_hostname": nodo_hostname,
            "nodo_url": nodo_url,
            "elegido_en": "now()"
        }).eq("id", 1).execute()
        return True
    except Exception as e:
        print(f"Error actualizando lider: {e}")
        return False


def obtener_lider() -> Optional[Dict[str, Any]]:
    """Obtener el nodo lider actual."""
    try:
        response = db.table("lider_actual").select("*").eq("id", 1).single().execute()
        return response.data if response.data else None
    except Exception as e:
        print(f"Error obteniendo lider: {e}")
        return None


def heartbeat_lider(nodo_id: int) -> bool:
    """Actualizar el ultimo heartbeat del lider."""
    try:
        db.table("lider_actual").update({
            "ultimo_heartbeat": "now()"
        }).eq("id", 1).eq("nodo_id", nodo_id).execute()
        return True
    except Exception as e:
        print(f"Error actualizando heartbeat: {e}")
        return False
