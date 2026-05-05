"""
Router principal del sistema.
Persistencia 100% en Supabase para autenticacion, areas y metadatos.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import hashlib
import os
import shutil
from typing import Any, Optional
import requests
import io

from master.auth import hashear_contrasena, verificar_contrasena, generar_token, requiere_admin
from master.gateway import validar_carga
from master.consensus import clasificar_con_consenso
from master.adapter import (
    adaptar_respuesta_carga,
    adaptar_respuesta_archivos,
)
from master.database import (
    db,
    obtener_usuario_por_nombre,
    obtener_usuario_por_id,
    insertar_usuario,
    crear_token_sesion,
    obtener_token,
    revocar_token,
    obtener_catalogo_global,
    obtener_categorias_globales,
    obtener_subtematicas,
    resolver_tema_predicho,
    insertar_documento,
    obtener_documentos_usuario,
    actualizar_documento_clasificacion,
    marcar_documento_eliminando,
    marcar_documento_eliminado,
    crear_solicitud_borrado_cola,
    obtener_solicitud_borrado_activa,
    obtener_solicitud_borrado_por_id,
    insertar_voto_consenso,
    insertar_nodo_replicacion,
    obtener_nodos_documento,
    marcar_nodo_inactivo,
)
from shared.cluster_config import obtener_nodos_cluster, obtener_url_nodo

router = APIRouter()

NODOS = ["node1", "node2", "node3"]
BASE_ALMACENAMIENTO = "../storage/"


def _parse_bearer(autorizacion: str) -> str:
    if not autorizacion.startswith("Bearer "):
        raise HTTPException(401, "Se requiere Authorization: Bearer <token>")
    return autorizacion[7:]


def _parse_iso_fecha(valor: str | None) -> datetime | None:
    if not valor:
        return None
    normalizado = valor.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalizado)
    except ValueError:
        return None


def _rol_id_por_nombre(nombre_rol: str) -> int:
    res = db.table("roles").select("id").eq("nombre", nombre_rol).single().execute()
    if not res.data:
        raise HTTPException(500, f"Rol '{nombre_rol}' no disponible en base de datos.")
    return res.data["id"]


def _rol_nombre_por_id(rol_id: int) -> str:
    res = db.table("roles").select("nombre").eq("id", rol_id).single().execute()
    if not res.data:
        return "user"
    return res.data["nombre"]


def _es_primer_usuario() -> bool:
    res = db.table("usuarios").select("id").limit(1).execute()
    return not bool(res.data)


def _obtener_documento_activo(
    usuario_id: str,
    nombre_archivo: str,
    tematica_id: str,
    subtematica_id: Optional[str],
) -> Optional[dict[str, Any]]:
    query = (
        db.table("documentos")
        .select("id, nombre_archivo, tematica_id, subtematica_id, estado")
        .eq("usuario_id", usuario_id)
        .eq("nombre_archivo", nombre_archivo)
        .eq("tematica_id", tematica_id)
        .eq("estado", "activo")
    )

    if subtematica_id:
        query = query.eq("subtematica_id", subtematica_id)
    else:
        query = query.is_("subtematica_id", "null")

    res = query.limit(1).execute()
    if not res.data:
        return None
    return res.data[0]


def usuario_actual(autorizacion: str = Header(...)) -> tuple[str, dict[str, Any]]:
    token = _parse_bearer(autorizacion)
    sesion = obtener_token(token)

    if not sesion:
        raise HTTPException(401, "Token invalido o sesion expirada.")

    expira_en = _parse_iso_fecha(sesion.get("expira_en"))
    ahora = datetime.now(timezone.utc)
    if expira_en and expira_en <= ahora:
        revocar_token(token)
        raise HTTPException(401, "Token expirado.")

    usuario = obtener_usuario_por_id(sesion["usuario_id"])
    if not usuario or not usuario.get("activo", True):
        raise HTTPException(401, "Usuario inactivo o inexistente.")

    rol = _rol_nombre_por_id(usuario["rol_id"])
    
    # Obtener catálogo global (ya no por usuario)
    categorias_globales = obtener_categorias_globales()

    return usuario["username"], {
        "id": usuario["id"],
        "username": usuario["username"],
        "role": rol,
        "categorias_globales": categorias_globales,
        "token": token,
    }


def obtener_admin(auth: tuple = Depends(usuario_actual)) -> tuple[str, dict[str, Any]]:
    nombre_usuario, datos = auth
    requiere_admin(datos)
    return nombre_usuario, datos


@router.post("/register", tags=["auth"])
def registrar(nombre_usuario: str, contrasena: str):
    if obtener_usuario_por_nombre(nombre_usuario):
        raise HTTPException(400, "El nombre de usuario ya existe.")
    if len(contrasena) < 6:
        raise HTTPException(400, "La contrasena debe tener al menos 6 caracteres.")

    rol = "admin" if _es_primer_usuario() else "user"
    rol_id = _rol_id_por_nombre(rol)

    usuario_id = insertar_usuario(
        username=nombre_usuario,
        password_hash=hashear_contrasena(contrasena),
        rol_id=rol_id,
    )
    if not usuario_id:
        raise HTTPException(500, "No se pudo registrar el usuario.")

    return {"mensaje": f"Usuario '{nombre_usuario}' registrado.", "rol": rol}


@router.post("/login", tags=["auth"])
def iniciar_sesion(nombre_usuario: str, contrasena: str):
    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if not usuario:
        raise HTTPException(401, "Usuario o contrasena incorrectos.")

    if not verificar_contrasena(contrasena, usuario["password_hash"]):
        raise HTTPException(401, "Usuario o contrasena incorrectos.")

    if not usuario.get("activo", True):
        raise HTTPException(403, "Usuario inactivo.")

    token = generar_token()
    expira_en = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace("+00:00", "Z")

    token_id = crear_token_sesion(usuario_id=usuario["id"], token_hash=token, expira_en=expira_en)
    if not token_id:
        raise HTTPException(500, "No se pudo crear la sesion.")

    return {
        "mensaje": "Sesion iniciada.",
        "token": token,
        "rol": _rol_nombre_por_id(usuario["rol_id"]),
    }


@router.post("/logout", tags=["auth"])
def cerrar_sesion(auth: tuple = Depends(usuario_actual)):
    _, datos = auth
    if not revocar_token(datos["token"]):
        raise HTTPException(500, "No se pudo cerrar la sesion.")
    return {"mensaje": "Sesion cerrada."}


@router.get("/categories", tags=["areas"])
def obtener_categorias(auth: tuple = Depends(usuario_actual)):
    """Obtener el catálogo global de categorías (solo lectura).
    
    Los usuarios NO pueden crear ni borrar categorías.
    El catálogo es fijo y administrado por el sistema.
    """
    _, datos = auth
    return {
        "mensaje": "Catálogo global de categorías",
        "categorias_globales": datos["categorias_globales"]
    }

# ELIMINADO: Los usuarios ya no pueden crear ni borrar categorías.
# El catálogo es global y de solo lectura.
# Endpoints removidos:
#   - POST /areas
#   - POST /areas/{area}/sub
#   - DELETE /areas/{area}
#   - DELETE /areas/{area}/sub/{subarea}


@router.post("/node-startup", tags=["cluster"])
def node_startup(node_name: str):
    """Endpoint para que workers notifiquen al master cuando se levantan.
    
    Patrón PUSH: Worker → Master (más eficiente que polling)
    
    Retorna los borrados pendientes para que el worker sincronice inmediatamente.
    Si no hay pendientes, retorna lista vacía.
    
    Args:
        node_name: Nombre del nodo que se levanta (ej: 'node1', 'node2', 'node3')
    
    Retorna:
        {
            "borrados_pendientes": [
                {
                    "id": "uuid",
                    "lista_archivos": [{...}],
                    "nodo_destino": "node1",
                    "estado": "pendiente"
                }
            ],
            "timestamp": "2026-05-04T10:30:45Z"
        }
    """
    from master.database import db
    
    try:
        # Obtener todos los borrados pendientes para este nodo
        resp = db.table("borrados_pendientes").select(
            "id, documento_id, lista_archivos, nodo_destino, estado"
        ).eq("estado", "pendiente").eq("nodo_destino", node_name).execute()
        
        borrados_pendientes = resp.data or []
        
        print(f"[NODE-STARTUP] {node_name} se levantó - {len(borrados_pendientes)} borrados pendientes")
        
        return {
            "mensaje": f"Node {node_name} registrado al startup",
            "borrados_pendientes": borrados_pendientes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"[NODE-STARTUP] Error: {e}")
        return {
            "mensaje": f"Error obteniendo pendientes para {node_name}",
            "borrados_pendientes": [],
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...), auth: tuple = Depends(usuario_actual)):
    """Cargar un archivo. Se clasificará automáticamente usando el catálogo global.
    
    El flujo es:
    1. Recibir archivo PDF del usuario
    2. Enviar a workers con catálogo global
    3. Consenso devuelve ruta predicha (ej: "Tecnología/Inteligencia Artificial")
    4. Validar que existe en catálogo
    5. Si no existe → asignar "Otros/General" automáticamente
    6. Guardar documento con IDs del catálogo y user_id del usuario
    """
    nombre_usuario, datos = auth
    validar_carga(archivo)

    # Obtener catálogo global
    categorias_globales = datos["categorias_globales"]
    if not categorias_globales:
        raise HTTPException(500, "Catálogo global vacío. Contacta al administrador.")

    ruta_temporal = f"temp_{nombre_usuario}_{archivo.filename}"
    with open(ruta_temporal, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    try:
        # Clasificar con consenso (ahora recibe catálogo global)
        ruta_predicha, votos = clasificar_con_consenso(ruta_temporal, categorias_globales)
        
        # Validar que la ruta predicha existe en catálogo
        tematica_id, subtematica_id = resolver_tema_predicho(ruta_predicha)
        
        # Si no existe, asignar fallback a "Otros/General"
        if tematica_id is None:
            print(f"[UPLOAD] Ruta predicha '{ruta_predicha}' no existe en catálogo. Asignando fallback 'Otros/General'")
            ruta_predicha = "Otros/General"
            tematica_id, subtematica_id = resolver_tema_predicho(ruta_predicha)
            
            if tematica_id is None:
                raise HTTPException(500, "No se puede resolver 'Otros/General' en catálogo. Contacta al administrador.")

        # Calcular hash del archivo
        hash_archivo = hashlib.sha256()
        with open(ruta_temporal, "rb") as f_hash:
            for chunk in iter(lambda: f_hash.read(8192), b""):
                hash_archivo.update(chunk)

        tamano_bytes = os.path.getsize(ruta_temporal)

        # Insertar documento con IDs del catálogo global
        # IMPORTANTE: usuario_id va en el documento para que solo ese usuario lo vea
        documento_id = insertar_documento(
            usuario_id=datos["id"],
            tematica_id=tematica_id,
            nombre_archivo=archivo.filename,
            hash_archivo=hash_archivo.hexdigest(),
            tamano_bytes=tamano_bytes,
            subtematica_id=subtematica_id,
        )
        if not documento_id:
            raise HTTPException(500, "No se pudo registrar el documento en base de datos.")

        # Replicar en nodos de almacenamiento
        nodos_almacenados: list[str] = []
        area_nombre, subarea_nombre = ruta_predicha.split("/")
        
        for nodo in NODOS:
            directorio_destino = os.path.join(
                BASE_ALMACENAMIENTO,
                nodo,
                nombre_usuario,
                area_nombre,
                subarea_nombre if subarea_nombre else "",
            )
            os.makedirs(directorio_destino, exist_ok=True)

            ruta_destino = os.path.join(directorio_destino, archivo.filename)
            shutil.copy(ruta_temporal, ruta_destino)
            nodos_almacenados.append(nodo)

            insertar_nodo_replicacion(documento_id, nodo, ruta_destino)

        # Registrar votos del consenso
        votos_validos = [v for v in votos.values() if v != "sin respuesta"]
        for nodo, ruta_voto in votos.items():
            if ruta_voto == "sin respuesta":
                continue
            insertar_voto_consenso(documento_id, nodo, ruta_voto, 0.0)

        # Calcular confianza basada en consenso
        confianza = 0.0
        if votos_validos:
            confianza = round(votos_validos.count(ruta_predicha) / len(votos_validos), 2)

        # Actualizar documento con clasificación final
        if subtematica_id:
            actualizar_documento_clasificacion(documento_id, subtematica_id, confianza)
        else:
            db.table("documentos").update(
                {
                    "confianza_clasificacion": confianza,
                    "clasificado_en": "now()",
                }
            ).eq("id", documento_id).execute()

        return adaptar_respuesta_carga(archivo.filename, area_nombre, subarea_nombre, nodos_almacenados, votos)
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@router.get("/files", tags=["documentos"])
def obtener_archivos(auth: tuple = Depends(usuario_actual)):
    """Obtener estructura de archivos del usuario clasificados en el catálogo global."""
    nombre_usuario, datos = auth

    # Obtener catálogo global
    catalogo_global = obtener_catalogo_global()
    if not catalogo_global:
        return adaptar_respuesta_archivos(nombre_usuario, {})

    # Construir árbol del catálogo global
    arbol: dict[str, Any] = {}
    for tematica in catalogo_global:
        tematica_id = tematica["id"]
        tematica_nombre = tematica["nombre"]
        arbol[tematica_nombre] = {"files": []}
        
        # Obtener subtematicas
        subtematicas = obtener_subtematicas(tematica_id)
        for sub in subtematicas:
            arbol[tematica_nombre][sub["nombre"]] = {"files": []}

    # Llenar árbol con documentos del usuario
    documentos = obtener_documentos_usuario(datos["id"])
    for doc in documentos:
        # Obtener tematica
        tematica_res = db.table("tematicas").select("nombre").eq("id", doc["tematica_id"]).single().execute()
        if not tematica_res.data:
            continue
        
        area_nombre = tematica_res.data["nombre"]
        
        # Obtener subtematica si existe
        sub_nombre = ""
        if doc.get("subtematica_id"):
            sub_res = db.table("subtematicas").select("nombre").eq("id", doc["subtematica_id"]).single().execute()
            if sub_res.data:
                sub_nombre = sub_res.data["nombre"]

        # Agregar archivo al árbol
        if area_nombre in arbol:
            if sub_nombre:
                if sub_nombre in arbol[area_nombre]:
                    arbol[area_nombre][sub_nombre]["files"].append(doc["nombre_archivo"])
            else:
                arbol[area_nombre]["files"].append(doc["nombre_archivo"])

    return adaptar_respuesta_archivos(nombre_usuario, arbol)


@router.get("/download", tags=["documentos"])
def descargar_archivo(
    nombre_archivo: str = Query(...),
    area: str = Query(...),
    subarea: Optional[str] = Query(None),
    auth: tuple = Depends(usuario_actual),
):
    """
    Descargar un archivo del usuario.
    
    ✅ PATRÓN REVERSE PROXY:
    1. El cliente pide el archivo al Líder
    2. El Líder consulta en BD qué nodos lo tienen
    3. El Líder hace HTTP request a un worker: /serve-file?...
    4. El Líder streamea la respuesta del worker al cliente
    5. Si el worker falla, intenta con el siguiente nodo
    
    Esto garantiza que el archivo se descarga aunque el Líder no lo tenga localmente.
    """
    nombre_usuario, datos = auth

    # Buscar documento del usuario con esos parámetros
    query = (
        db.table("documentos")
        .select("id, tematica_id, subtematica_id, nombre_archivo")
        .eq("usuario_id", datos["id"])
        .eq("nombre_archivo", nombre_archivo)
        .eq("estado", "activo")
    )

    # Obtener tematica_id del área
    tematica_res = db.table("tematicas").select("id").eq("nombre", area).single().execute()
    if not tematica_res.data:
        raise HTTPException(404, f"Área '{area}' no encontrada.")
    
    query = query.eq("tematica_id", tematica_res.data["id"])

    # Si se especifica subárea, filtrar por ella
    if subarea:
        subtematica_res = db.table("subtematicas").select("id").eq("tematica_id", tematica_res.data["id"]).eq("nombre", subarea).single().execute()
        if not subtematica_res.data:
            raise HTTPException(404, f"Subárea '{subarea}' no encontrada.")
        query = query.eq("subtematica_id", subtematica_res.data["id"])
    else:
        query = query.is_("subtematica_id", "null")

    res = query.limit(1).execute()
    if not res.data:
        raise HTTPException(404, "Documento no encontrado.")

    documento = res.data[0]
    nodos_documento = obtener_nodos_documento(documento["id"])
    
    if not nodos_documento:
        raise HTTPException(404, "No hay réplicas del archivo en ningún nodo.")
    
    # Intentar obtener del archivo desde cada nodo (Patrón: Reverse Proxy)
    subarea_param = subarea if subarea else ""
    
    for nodo_info in nodos_documento:
        nodo_id = nodo_info.get("nodo_id")
        
        try:
            # Obtener URL del nodo
            url_nodo = obtener_url_nodo(nodo_id)
            url_serve = f"{url_nodo}/serve-file"
            
            # Hacer request HTTP al worker
            params = {
                "nombre_usuario": nombre_usuario,
                "area": area,
                "subarea": subarea_param,
                "nombre_archivo": nombre_archivo,
            }
            
            respuesta = requests.get(url_serve, params=params, timeout=10, stream=True)
            
            if respuesta.status_code == 200:
                # ✅ Éxito: streamear el archivo del worker al cliente
                def generar():
                    for chunk in respuesta.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                
                return StreamingResponse(
                    generar(),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
                )
            elif respuesta.status_code == 404:
                # Nodo no tiene el archivo, intentar siguiente
                continue
            else:
                # Error en el nodo, intentar siguiente
                print(f"[DOWNLOAD] Nodo {nodo_id} retornó {respuesta.status_code}")
                continue
        
        except requests.exceptions.Timeout:
            print(f"[DOWNLOAD] Timeout contactando nodo {nodo_id}")
            continue
        except requests.exceptions.ConnectionError:
            print(f"[DOWNLOAD] Nodo {nodo_id} no disponible")
            continue
        except Exception as e:
            print(f"[DOWNLOAD] Error con nodo {nodo_id}: {e}")
            continue
    
    # Si llegamos aquí, ningún nodo respondió
    raise HTTPException(503, "Todos los nodos están offline. Reintenta en unos momentos.")


@router.delete("/document", tags=["documentos"])
def eliminar_documento(
    nombre_archivo: str,
    area: str,
    subarea: Optional[str] = None,
    auth: tuple = Depends(usuario_actual),
):
    """Encolar la solicitud de borrado del documento del usuario.

    Flujo:
      1. Validar que el documento existe y pertenece al usuario
      2. Guardar la solicitud en cola_borrados
      3. Responder 202 Accepted
      4. El master procesa la cola en segundo plano
    """
    nombre_usuario, datos = auth

    # Buscar documento del usuario
    query = (
        db.table("documentos")
        .select("id")
        .eq("usuario_id", datos["id"])
        .eq("nombre_archivo", nombre_archivo)
        .eq("estado", "activo")
    )

    # Obtener tematica_id del área
    tematica_res = db.table("tematicas").select("id").eq("nombre", area).single().execute()
    if not tematica_res.data:
        raise HTTPException(404, f"Área '{area}' no encontrada.")
    
    query = query.eq("tematica_id", tematica_res.data["id"])

    # Si se especifica subárea, filtrar por ella
    if subarea:
        subtematica_res = db.table("subtematicas").select("id").eq("tematica_id", tematica_res.data["id"]).eq("nombre", subarea).single().execute()
        if not subtematica_res.data:
            raise HTTPException(404, f"Subárea '{subarea}' no encontrada.")
        query = query.eq("subtematica_id", subtematica_res.data["id"])
    else:
        query = query.is_("subtematica_id", "null")

    res = query.limit(1).execute()
    if not res.data:
        raise HTTPException(404, "Documento no encontrado.")

    documento = res.data[0]
    nodos = obtener_nodos_documento(documento["id"])

    lista_archivos: list[dict] = []
    if nodos:
        for nodo in nodos:
            ruta_fisica = nodo.get("ruta_fisica") or ""
            if not ruta_fisica:
                continue
            partes = ruta_fisica.replace("\\", "/").split("/")
            if len(partes) >= 4:
                lista_archivos.append(
                    {
                        "nombre_usuario": partes[-4],
                        "area": partes[-3],
                        "subarea": "" if partes[-2] == "" else partes[-2],
                        "nombre": partes[-1],
                    }
                )

    if not lista_archivos:
        ruta_sub = subarea if subarea else ""
        for nodo in NODOS:
            ruta = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, ruta_sub, nombre_archivo)
            if os.path.exists(ruta):
                lista_archivos.append(
                    {
                        "nombre_usuario": nombre_usuario,
                        "area": area,
                        "subarea": ruta_sub,
                        "nombre": nombre_archivo,
                    }
                )

    if not lista_archivos:
        raise HTTPException(404, "Archivo no encontrado en ningun nodo.")

    solicitud_activa = obtener_solicitud_borrado_activa(documento["id"])
    if solicitud_activa:
        return JSONResponse(
            status_code=202,
            content={
                "mensaje": f"La solicitud de borrado de '{nombre_archivo}' ya está en cola.",
                "estado": "aceptada",
                "cola_id": solicitud_activa["id"],
                "documento_id": documento["id"],
            },
        )

    cola_id = crear_solicitud_borrado_cola(
        documento_id=documento["id"],
        usuario_id=datos["id"],
        nombre_usuario=nombre_usuario,
        nombre_archivo=nombre_archivo,
        area=area,
        subarea=subarea,
    )

    if not cola_id:
        raise HTTPException(503, "No se pudo encolar la solicitud de borrado.")

    return JSONResponse(
        status_code=202,
        content={
            "mensaje": f"Solicitud de borrado de '{nombre_archivo}' aceptada y encolada.",
            "estado": "aceptada",
            "cola_id": cola_id,
            "documento_id": documento["id"],
        },
    )


@router.get("/delete-requests/{cola_id}", tags=["documentos"])
def obtener_estado_solicitud_borrado(cola_id: str, auth: tuple = Depends(usuario_actual)):
    """Consultar el estado de una solicitud de borrado en la cola.

    Retorna detalles básicos: estado, intentos, ultimo_error, timestamps.
    Solo el usuario que inició la solicitud puede consultarla.
    """
    nombre_usuario, datos = auth

    solicitud = obtener_solicitud_borrado_por_id(cola_id)
    if not solicitud:
        raise HTTPException(404, "Solicitud no encontrada.")

    # Permiso: solo el propietario puede consultar su solicitud
    if solicitud.get("usuario_id") != datos["id"]:
        raise HTTPException(403, "No tienes permiso para ver esta solicitud.")

    return {
        "cola_id": solicitud.get("id"),
        "documento_id": solicitud.get("documento_id"),
        "estado": solicitud.get("estado"),
        "intentos": solicitud.get("intentos", 0),
        "ultimo_error": solicitud.get("ultimo_error"),
        "creado_en": solicitud.get("creado_en"),
        "actualizado_en": solicitud.get("actualizado_en"),
    }


@router.get("/admin/users", tags=["admin"])
def listar_usuarios(auth: tuple = Depends(obtener_admin)):
    _ = auth
    usuarios = db.table("usuarios").select("id, username, rol_id, activo").execute().data or []
    
    # Obtener catálogo global
    categorias_globales = obtener_categorias_globales()

    respuesta = {}
    for usuario in usuarios:
        rol = _rol_nombre_por_id(usuario["rol_id"])
        respuesta[usuario["username"]] = {
            "rol": rol,
            "activo": usuario.get("activo", True),
            "categorias_globales": categorias_globales,
        }

    return respuesta


@router.post("/admin/users", tags=["admin"])
def admin_crear_usuario(
    nombre_usuario: str,
    contrasena: str,
    rol: str = "user",
    auth: tuple = Depends(obtener_admin),
):
    _ = auth
    if rol not in ("user", "admin"):
        raise HTTPException(400, "Rol invalido. Usa 'user' o 'admin'.")
    if len(contrasena) < 6:
        raise HTTPException(400, "La contrasena debe tener al menos 6 caracteres.")
    if obtener_usuario_por_nombre(nombre_usuario):
        raise HTTPException(400, "El nombre de usuario ya existe.")

    rol_id = _rol_id_por_nombre(rol)
    usuario_id = insertar_usuario(
        username=nombre_usuario,
        password_hash=hashear_contrasena(contrasena),
        rol_id=rol_id,
    )
    if not usuario_id:
        raise HTTPException(500, "No se pudo crear el usuario.")

    return {"mensaje": f"Usuario '{nombre_usuario}' creado con rol '{rol}'."}


@router.delete("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_eliminar_usuario(nombre_usuario: str, auth: tuple = Depends(obtener_admin)):
    admin_user, _ = auth
    if nombre_usuario == admin_user:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta.")

    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")

    for nodo in NODOS:
        dir_usuario = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario)
        if os.path.exists(dir_usuario):
            shutil.rmtree(dir_usuario)

    db.table("usuarios").delete().eq("id", usuario["id"]).execute()
    return {"mensaje": f"Usuario '{nombre_usuario}' eliminado."}


@router.put("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_actualizar_usuario(
    nombre_usuario: str,
    nuevo_nombre_usuario: Optional[str] = None,
    nueva_contrasena: Optional[str] = None,
    nuevo_rol: Optional[str] = None,
    auth: tuple = Depends(obtener_admin),
):
    _ = auth

    if not nuevo_nombre_usuario and not nueva_contrasena and not nuevo_rol:
        raise HTTPException(400, "Debes proporcionar al menos un campo a actualizar.")

    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")

    campos: dict[str, Any] = {}

    if nuevo_nombre_usuario and nuevo_nombre_usuario != nombre_usuario:
        if obtener_usuario_por_nombre(nuevo_nombre_usuario):
            raise HTTPException(400, "El nuevo nombre de usuario ya existe.")

        for nodo in NODOS:
            dir_antiguo = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario)
            dir_nuevo = os.path.join(BASE_ALMACENAMIENTO, nodo, nuevo_nombre_usuario)
            if os.path.exists(dir_antiguo):
                os.rename(dir_antiguo, dir_nuevo)

        campos["username"] = nuevo_nombre_usuario

    if nueva_contrasena:
        if len(nueva_contrasena) < 6:
            raise HTTPException(400, "La contrasena debe tener al menos 6 caracteres.")
        campos["password_hash"] = hashear_contrasena(nueva_contrasena)
        db.table("tokens_sesion").update({"revocado": True}).eq("usuario_id", usuario["id"]).execute()

    if nuevo_rol:
        if nuevo_rol not in ("user", "admin"):
            raise HTTPException(400, "Rol invalido. Usa 'user' o 'admin'.")
        campos["rol_id"] = _rol_id_por_nombre(nuevo_rol)

    if campos:
        db.table("usuarios").update(campos).eq("id", usuario["id"]).execute()

    return {
        "mensaje": "Usuario actualizado correctamente.",
        "nombre_usuario": nuevo_nombre_usuario or nombre_usuario,
    }




# ELIMINADO: Los endpoints de eliminar áreas fueron removidos porque 
# el catálogo global de temáticas es de solo lectura y no puede ser modificado 
# por usuarios ni administradores.
# 
# Endpoints removidos:
#   - DELETE /admin/areas/{nombre_usuario}/{area}
#   - DELETE /admin/areas/{nombre_usuario}/{area}/{subarea}
