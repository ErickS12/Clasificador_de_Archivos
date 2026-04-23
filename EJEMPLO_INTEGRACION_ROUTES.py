"""
EJEMPLO: Como integrar database.py en routes.py

Este archivo muestra un ejemplo de integracion paso a paso.
NO es codigo listo para produccion - es para entendimiento.

ARCHIVO: master/routes.py (VERSION SUPABASE)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from fastapi.responses import FileResponse
import os
import hashlib
from datetime import datetime, timedelta

# ── IMPORTAR FUNCIONES DE DATABASE ─────────────────────────────────────────

from master.auth import (
    hashear_contrasena,
    verificar_contrasena,
    generar_token,
    obtener_usuario_del_token
)
from master.gateway import validar_carga
from master.consensus import clasificar_con_consenso
from master.adapter import (
    adaptar_respuesta_carga,
    resolver_area,
    construir_areas_planas
)

# NUEVO: Importar funciones Supabase
from master.database import (
    # Usuarios
    obtener_usuario_por_nombre,
    insertar_usuario,
    obtener_usuario_por_id,
    # Tokens
    crear_token_sesion,
    obtener_token,
    revocar_token,
    # Tematicas
    obtener_tematicas_usuario,
    insertar_tematica,
    obtener_subtematicas,
    insertar_subtematica,
    # Documentos
    insertar_documento,
    obtener_documentos_usuario,
    actualizar_documento_clasificacion,
    marcar_documento_eliminando,
    marcar_documento_eliminado,
    # Nodos
    insertar_nodo_replicacion,
    obtener_nodos_documento,
    marcar_nodo_verificado,
    # Consenso
    insertar_voto_consenso,
    obtener_votos_documento,
)

router = APIRouter()

# Configuracion
NODOS = ["node1", "node2", "node3"]
BASE_ALMACENAMIENTO = "../storage/"


# ══════════════════════════════════════════════════════════════════════════
# AUTENTICACION
# ══════════════════════════════════════════════════════════════════════════

@router.post("/register")
def registrar_usuario(username: str, password: str):
    """
    Registrar nuevo usuario.
    
    Flujo:
    1. Verificar que username no existe en BD
    2. Hashear contrasena
    3. Insertar usuario en tabla usuarios
    4. AUTOMATICO: trigger crea tematica 'General'
    """
    
    # 1. Verificar que no existe
    usuario_existente = obtener_usuario_por_nombre(username)
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    # 2. Hashear contrasena
    password_hash = hashear_contrasena(password)
    
    # 3. NUEVO: Insertar en Supabase
    usuario_id = insertar_usuario(
        username=username,
        password_hash=password_hash,
        rol_id=2  # rol: user
    )
    
    if not usuario_id:
        raise HTTPException(status_code=500, detail="Error creando usuario")
    
    return {
        "usuario_id": usuario_id,
        "username": username,
        "mensaje": "Usuario creado. La tematica 'General' fue creada automaticamente."
    }


@router.post("/login")
def login(username: str, password: str):
    """
    Login y generar token.
    
    Flujo:
    1. Buscar usuario en BD por username
    2. Verificar contrasena
    3. Generar token UUID
    4. Guardar token_hash en tabla tokens_sesion
    5. Retornar token al cliente
    """
    
    # 1. NUEVO: Buscar en Supabase
    usuario = obtener_usuario_por_nombre(username)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos")
    
    # 2. Verificar contrasena
    if not verificar_contrasena(password, usuario['password_hash']):
        raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos")
    
    # 3. Generar token
    token = generar_token()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # 4. NUEVO: Guardar token en Supabase (24h de duracion por DEFAULT)
    expira_en = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
    token_id = crear_token_sesion(
        usuario_id=usuario['id'],
        token_hash=token_hash,
        expira_en=expira_en
    )
    
    if not token_id:
        raise HTTPException(status_code=500, detail="Error creando sesion")
    
    return {
        "token": token,
        "usuario_id": usuario['id'],
        "username": usuario['username'],
        "expires_in": 86400  # 24 horas en segundos
    }


@router.post("/logout")
def logout(authorization: str = Header(...)):
    """
    Logout y revocar token.
    
    Flujo:
    1. Extraer token del header
    2. Hashear para buscar en BD
    3. Marcar como revocado
    """
    
    token = authorization.replace("Bearer ", "")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # NUEVO: Revocar en Supabase
    if revocar_token(token_hash):
        return {"mensaje": "Sesion cerrada"}
    else:
        raise HTTPException(status_code=500, detail="Error cerrando sesion")


# ══════════════════════════════════════════════════════════════════════════
# UPLOAD Y CLASIFICACION
# ══════════════════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_documento(
    file: UploadFile = File(...),
    tematica_id: str = None,
    authorization: str = Header(...)
):
    """
    Subir documento PDF y clasificarlo.
    
    Flujo:
    1. Autenticar usuario
    2. Validar PDF
    3. Crear registro en tabla documentos
    4. Replicar en 3 nodos (node1, node2, node3)
    5. Clasificar con consenso de workers
    6. Guardar votos en tabla consenso_votos
    7. Actualizar documento con clasificacion final
    8. Retornar resultado al cliente
    """
    
    # 1. Autenticar
    token = authorization.replace("Bearer ", "")
    usuario = obtener_usuario_del_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # 2. Validar PDF
    await validar_carga(file)
    
    # Leer contenido del archivo
    contenido = await file.read()
    hash_archivo = hashlib.sha256(contenido).hexdigest()
    
    # 3. NUEVO: Crear documento en BD
    tematica_id = tematica_id or "general"  # Si no especifica, usar General
    
    doc_id = insertar_documento(
        usuario_id=usuario['id'],
        tematica_id=tematica_id,
        nombre_archivo=file.filename,
        hash_archivo=hash_archivo,
        tamano_bytes=len(contenido),
        subtematica_id=None  # Se llenara despues de clasificar
    )
    
    if not doc_id:
        raise HTTPException(status_code=500, detail="Error creando documento")
    
    # 4. Replicar en 3 nodos
    nodos_replicados = []
    for nodo in NODOS:
        try:
            ruta_fisica = os.path.join(BASE_ALMACENAMIENTO, nodo, f"{doc_id}.pdf")
            os.makedirs(os.path.dirname(ruta_fisica), exist_ok=True)
            
            with open(ruta_fisica, 'wb') as f:
                f.write(contenido)
            
            # NUEVO: Registrar nodo en BD
            insertar_nodo_replicacion(
                documento_id=doc_id,
                nodo=nodo,
                ruta_fisica=ruta_fisica
            )
            
            nodos_replicados.append(nodo)
        except Exception as e:
            print(f"Error replicando en {nodo}: {e}")
    
    # 5. Clasificar con consenso
    try:
        # Llamar a los 3 workers
        clasificaciones = clasificar_con_consenso(contenido)
        
        # 6. NUEVO: Guardar votos en tabla consenso_votos
        for nodo_worker, resultado in clasificaciones.items():
            insertar_voto_consenso(
                documento_id=doc_id,
                nodo_worker=nodo_worker,
                area_predicha=resultado['area'],
                confianza_worker=resultado.get('confianza', 0.0)
            )
        
        # 7. Calcular consenso (mayoría)
        areas = [c['area'] for c in clasificaciones.values()]
        area_final = max(set(areas), key=areas.count)  # Moda
        
        # Obtener ID de subtematica
        subtematicas = obtener_subtematicas(tematica_id)
        subtematica_final = next(
            (s for s in subtematicas if s['nombre'] == area_final),
            None
        )
        
        if subtematica_final:
            # 8. NUEVO: Actualizar documento con clasificacion
            actualizar_documento_clasificacion(
                documento_id=doc_id,
                subtematica_id=subtematica_final['id'],
                confianza=0.67  # Consenso de 2/3 workers
            )
        
    except Exception as e:
        print(f"Error en clasificacion: {e}")
        return {
            "documento_id": doc_id,
            "estado": "error_clasificacion",
            "detalle": str(e)
        }
    
    return {
        "documento_id": doc_id,
        "nombre_archivo": file.filename,
        "clasificacion": area_final,
        "confianza": 0.67,
        "nodos_replicados": nodos_replicados,
        "estado": "clasificado"
    }


# ══════════════════════════════════════════════════════════════════════════
# GESTION DE ARCHIVOS
# ══════════════════════════════════════════════════════════════════════════

@router.get("/documentos")
def listar_documentos(authorization: str = Header(...)):
    """
    Listar documentos del usuario.
    
    Flujo:
    1. Autenticar
    2. NUEVO: Consultar tabla documentos donde estado='activo'
    3. Retornar lista con detalles
    """
    
    token = authorization.replace("Bearer ", "")
    usuario = obtener_usuario_del_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # NUEVO: Obtener de BD
    documentos = obtener_documentos_usuario(usuario['id'])
    
    return {
        "total": len(documentos),
        "documentos": documentos
    }


@router.delete("/documentos/{doc_id}")
def eliminar_documento(doc_id: str, authorization: str = Header(...)):
    """
    Eliminar documento (borrado en 2 pasos).
    
    Paso 1: Marcar como 'eliminando' + timestamp
    Paso 2: Workers confirman borrado fisico
    
    Flujo:
    1. Autenticar
    2. NUEVO: Marcar documento estado='eliminando'
    3. Retornar confirmacion (workers lo completaran)
    """
    
    token = authorization.replace("Bearer ", "")
    usuario = obtener_usuario_del_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # NUEVO: Marcar como eliminando
    if marcar_documento_eliminando(doc_id):
        return {
            "documento_id": doc_id,
            "estado": "eliminando",
            "mensaje": "Documento marcado para eliminacion. Los workers completaran el borrado."
        }
    else:
        raise HTTPException(status_code=500, detail="Error eliminando documento")


# ══════════════════════════════════════════════════════════════════════════
# TEMATICAS Y SUBTEMATICAS
# ══════════════════════════════════════════════════════════════════════════

@router.get("/tematicas")
def listar_tematicas(authorization: str = Header(...)):
    """
    Listar tematicas y subtematicas del usuario.
    """
    
    token = authorization.replace("Bearer ", "")
    usuario = obtener_usuario_del_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # NUEVO: Obtener tematicas de BD
    tematicas = obtener_tematicas_usuario(usuario['id'])
    
    # Enriquecer con subtematicas
    for tematica in tematicas:
        tematica['subtematicas'] = obtener_subtematicas(tematica['id'])
    
    return {"tematicas": tematicas}


@router.post("/tematicas")
def crear_tematica(
    nombre: str,
    authorization: str = Header(...)
):
    """
    Crear nueva tematica.
    """
    
    token = authorization.replace("Bearer ", "")
    usuario = obtener_usuario_del_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # NUEVO: Insertar en BD
    tematica_id = insertar_tematica(
        usuario_id=usuario['id'],
        nombre=nombre,
        es_general=False
    )
    
    if not tematica_id:
        raise HTTPException(status_code=500, detail="Error creando tematica")
    
    return {
        "tematica_id": tematica_id,
        "nombre": nombre
    }


# ══════════════════════════════════════════════════════════════════════════
# NOTAS
# ══════════════════════════════════════════════════════════════════════════

"""
CAMBIOS PRINCIPALES:

1. Persistencia en Supabase
    - Autenticacion, jerarquia y metadatos viven en tablas PostgreSQL
    - Los documentos replicados se registran en nodos_almacenamiento

2. Persistencia automática
   - Triggers crean tematica 'General' al registrar usuario
   - Trigger auto-actualiza heartbeat en lider_actual

3. Auditoria completa
   - Todos los cambios quedan registrados en BD
   - No se pierden datos (soft deletes)

4. Distribucion explicita
   - Consenso_votos registra el voto de cada worker
   - Nodos_almacenamiento registra donde esta replicado

5. Seguridad mejorada
   - Tokens con expiracion (24h default)
   - Token_hash almacenado (no el token en claro)
   - RLS puede activarse despues para row-level security
"""
