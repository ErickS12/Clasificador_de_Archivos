"""
Router principal del sistema.
Persistencia 100% en Supabase para autenticacion, areas y metadatos.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import FileResponse
import hashlib
import os
import shutil
from typing import Any, Optional

from master.auth import hashear_contrasena, verificar_contrasena, generar_token, requiere_admin
from master.gateway import validar_carga
from master.consensus import clasificar_con_consenso
from master.adapter import (
    adaptar_respuesta_carga,
    adaptar_respuesta_archivos,
    resolver_area,
    construir_areas_planas,
)
from master.database import (
    db,
    obtener_usuario_por_nombre,
    obtener_usuario_por_id,
    insertar_usuario,
    crear_token_sesion,
    obtener_token,
    revocar_token,
    obtener_tematicas_usuario,
    insertar_tematica,
    obtener_subtematicas,
    insertar_subtematica,
    insertar_documento,
    obtener_documentos_usuario,
    actualizar_documento_clasificacion,
    marcar_documento_eliminando,
    marcar_documento_eliminado,
    insertar_voto_consenso,
    insertar_nodo_replicacion,
    obtener_nodos_documento,
    marcar_nodo_inactivo,
)

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


def _catalogo_areas_usuario(usuario_id: str) -> dict[str, Any]:
    tematicas = obtener_tematicas_usuario(usuario_id)

    areas: dict[str, list[str]] = {}
    tematicas_por_nombre: dict[str, dict[str, Any]] = {}
    tematicas_por_id: dict[str, dict[str, Any]] = {}
    subtematicas_por_llave: dict[tuple[str, str], dict[str, Any]] = {}
    subtematicas_por_id: dict[str, dict[str, Any]] = {}

    for tematica in tematicas:
        t_id = tematica["id"]
        t_nombre = tematica["nombre"]
        tematicas_por_nombre[t_nombre] = tematica
        tematicas_por_id[t_id] = tematica

        subtematicas = obtener_subtematicas(t_id)
        areas[t_nombre] = [s["nombre"] for s in subtematicas]

        for sub in subtematicas:
            subtematicas_por_llave[(t_id, sub["nombre"])] = sub
            subtematicas_por_id[sub["id"]] = sub

    if "General" not in areas:
        areas["General"] = []

    return {
        "areas": areas,
        "tematicas_por_nombre": tematicas_por_nombre,
        "tematicas_por_id": tematicas_por_id,
        "subtematicas_por_llave": subtematicas_por_llave,
        "subtematicas_por_id": subtematicas_por_id,
    }


def _resolver_ids_area(
    usuario_id: str,
    area: str,
    subarea: Optional[str] = None,
) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
    catalogo = _catalogo_areas_usuario(usuario_id)
    tematica = catalogo["tematicas_por_nombre"].get(area)
    if not tematica:
        raise HTTPException(404, f"El area '{area}' no existe.")

    subtematica = None
    if subarea:
        subtematica = catalogo["subtematicas_por_llave"].get((tematica["id"], subarea))
        if not subtematica:
            raise HTTPException(404, f"La subarea '{subarea}' no existe en '{area}'.")

    return tematica, subtematica


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


def usuario_actual(authorization: str = Header(...)) -> tuple[str, dict[str, Any]]:
    token = _parse_bearer(authorization)
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
    catalogo = _catalogo_areas_usuario(usuario["id"])

    return usuario["username"], {
        "id": usuario["id"],
        "username": usuario["username"],
        "role": rol,
        "areas": catalogo["areas"],
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
    _, datos = auth
    return {"areas": datos["areas"]}

@router.post("/areas/{area}/sub", tags=["areas"])
def crear_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    _, datos = auth

    if area == "General":
        raise HTTPException(
            400,
            "El area 'General' no puede tener subareas."
        )

    tematica, _ = _resolver_ids_area(datos["id"], area)

    sub_existente = (
        db.table("subtematicas")
        .select("id")
        .eq("tematica_id", tematica["id"])
        .eq("nombre", subarea)
        .limit(1)
        .execute()
    )

    ...

@router.post("/areas/{area}/sub", tags=["areas"])
def crear_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    _, datos = auth
    tematica, _ = _resolver_ids_area(datos["id"], area)

    sub_existente = (
        db.table("subtematicas")
        .select("id")
        .eq("tematica_id", tematica["id"])
        .eq("nombre", subarea)
        .limit(1)
        .execute()
    )
    if sub_existente.data:
        raise HTTPException(400, f"La subarea '{subarea}' ya existe en '{area}'.")

    nueva_sub = insertar_subtematica(tematica["id"], subarea)
    if not nueva_sub:
        raise HTTPException(500, "No se pudo crear la subarea.")

    return {"mensaje": f"Subarea '{subarea}' creada en '{area}'."}


@router.delete("/areas/{area}", tags=["areas"])
def eliminar_area(area: str, auth: tuple = Depends(usuario_actual)):
    _, datos = auth
    if area == "General":
        raise HTTPException(400, "No se puede eliminar el area 'General'.")

    tematica, _ = _resolver_ids_area(datos["id"], area)

    docs = (
        db.table("documentos")
        .select("id")
        .eq("usuario_id", datos["id"])
        .eq("tematica_id", tematica["id"])
        .eq("estado", "activo")
        .limit(1)
        .execute()
    )
    if docs.data:
        raise HTTPException(400, f"El area '{area}' contiene documentos. Eliminalos primero.")

    db.table("tematicas").delete().eq("id", tematica["id"]).execute()
    return {"mensaje": f"Area '{area}' eliminada."}


@router.delete("/areas/{area}/sub/{subarea}", tags=["areas"])
def eliminar_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    _, datos = auth
    _, sub = _resolver_ids_area(datos["id"], area, subarea)

    docs = (
        db.table("documentos")
        .select("id")
        .eq("usuario_id", datos["id"])
        .eq("subtematica_id", sub["id"])
        .eq("estado", "activo")
        .limit(1)
        .execute()
    )
    if docs.data:
        raise HTTPException(400, f"La subarea '{subarea}' contiene documentos. Eliminalos primero.")

    db.table("subtematicas").delete().eq("id", sub["id"]).execute()
    return {"mensaje": f"Subarea '{subarea}' eliminada de '{area}'."}


@router.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...), auth: tuple = Depends(usuario_actual)):
    nombre_usuario, datos = auth
    validar_carga(archivo)

    catalogo = _catalogo_areas_usuario(datos["id"])
    areas_usuario = catalogo["areas"]
    areas_planas = construir_areas_planas(areas_usuario)

    ruta_temporal = f"temp_{nombre_usuario}_{archivo.filename}"
    with open(ruta_temporal, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    try:
        predicho, votos = clasificar_con_consenso(ruta_temporal, areas_planas)
        area, subarea = resolver_area(predicho, areas_usuario)

        tematica = catalogo["tematicas_por_nombre"].get(area)
        if not tematica:
            raise HTTPException(500, f"No existe la tematica destino '{area}' en base de datos.")

        subtematica_id = None
        if subarea:
            sub = catalogo["subtematicas_por_llave"].get((tematica["id"], subarea))
            if not sub:
                raise HTTPException(500, f"No existe la subarea destino '{subarea}' en base de datos.")
            subtematica_id = sub["id"]

        hash_archivo = hashlib.sha256()
        with open(ruta_temporal, "rb") as f_hash:
            for chunk in iter(lambda: f_hash.read(8192), b""):
                hash_archivo.update(chunk)

        tamano_bytes = os.path.getsize(ruta_temporal)

        documento_id = insertar_documento(
            usuario_id=datos["id"],
            tematica_id=tematica["id"],
            nombre_archivo=archivo.filename,
            hash_archivo=hash_archivo.hexdigest(),
            tamano_bytes=tamano_bytes,
            subtematica_id=subtematica_id,
        )
        if not documento_id:
            raise HTTPException(500, "No se pudo registrar el documento en base de datos.")

        nodos_almacenados: list[str] = []
        for nodo in NODOS:
            directorio_destino = os.path.join(
                BASE_ALMACENAMIENTO,
                nodo,
                nombre_usuario,
                area,
                subarea if subarea else "",
            )
            os.makedirs(directorio_destino, exist_ok=True)

            ruta_destino = os.path.join(directorio_destino, archivo.filename)
            shutil.copy(ruta_temporal, ruta_destino)
            nodos_almacenados.append(nodo)

            insertar_nodo_replicacion(documento_id, nodo, ruta_destino)

        votos_validos = [v for v in votos.values() if v != "sin respuesta"]
        for nodo, area_predicha in votos.items():
            if area_predicha == "sin respuesta":
                continue
            insertar_voto_consenso(documento_id, nodo, area_predicha, 0.0)

        confianza = 0.0
        if votos_validos:
            confianza = round(votos_validos.count(predicho) / len(votos_validos), 2)

        if subtematica_id:
            actualizar_documento_clasificacion(documento_id, subtematica_id, confianza)
        else:
            db.table("documentos").update(
                {
                    "confianza_clasificacion": confianza,
                    "clasificado_en": "now()",
                }
            ).eq("id", documento_id).execute()

        #return adaptar_respuesta_carga(archivo.filename, area, subarea, nodos_almacenados, votos),
        
        return {
                "id": documento_id,
                "area": area,
                "subarea": subarea,
                "nodos": nodos_almacenados,
                "votos": votos
            }
    
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@router.get("/files", tags=["documentos"])
def obtener_archivos(auth: tuple = Depends(usuario_actual)):
    nombre_usuario, datos = auth

    catalogo = _catalogo_areas_usuario(datos["id"])
    arbol: dict[str, Any] = {}
    for area, subareas in catalogo["areas"].items():
        arbol[area] = {"files": []}
        for sub in subareas:
            arbol[area][sub] = {"files": []}

    documentos = obtener_documentos_usuario(datos["id"])
    for doc in documentos:
        area_obj = catalogo["tematicas_por_id"].get(doc["tematica_id"])
        if not area_obj:
            continue

        area_nombre = area_obj["nombre"]
        sub_id = doc.get("subtematica_id")
        sub_nombre = ""
        if sub_id:
            sub_obj = catalogo["subtematicas_por_id"].get(sub_id)
            sub_nombre = sub_obj["nombre"] if sub_obj else ""

        arbol.setdefault(area_nombre, {"files": []})

        documento_info = {
            "id": doc["id"],
            "nombre": doc["nombre_archivo"],
            "fecha": doc.get("subido_en"),
            "area": area_nombre,
            "subarea": sub_nombre if sub_nombre else None,
        }
        if sub_nombre:
            arbol[area_nombre].setdefault(sub_nombre, {"files": []})
            arbol[area_nombre][sub_nombre]["files"].append(documento_info)
        else:
            arbol[area_nombre]["files"].append(documento_info)

    return adaptar_respuesta_archivos(nombre_usuario, arbol)


@router.get("/download", tags=["documentos"])
def descargar_archivo(
    nombre_archivo: str = Query(...),
    area: str = Query(...),
    subarea: Optional[str] = Query(None),
    auth: tuple = Depends(usuario_actual),
):
    subarea = subarea or None
    nombre_usuario, datos = auth
    tematica, subtematica = _resolver_ids_area(datos["id"], area, subarea)

    documento = _obtener_documento_activo(
        datos["id"],
        nombre_archivo,
        tematica["id"],
        subtematica["id"] if subtematica else None,
    )
    if not documento:
        raise HTTPException(404, "Documento no encontrado en base de datos.")

    nodos = obtener_nodos_documento(documento["id"])
    for nodo in nodos:
        ruta = nodo.get("ruta_fisica")
        if ruta and os.path.exists(ruta):
            return FileResponse(ruta, media_type="application/pdf", filename=nombre_archivo)

    ruta_sub = subarea if subarea else ""
    for nodo in NODOS:
        ruta = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, ruta_sub, nombre_archivo)
        if os.path.exists(ruta):
            return FileResponse(ruta, media_type="application/pdf", filename=nombre_archivo)

    raise HTTPException(404, "Archivo no encontrado en ningun nodo.")


@router.delete("/document", tags=["documentos"])
def eliminar_documento(
    nombre_archivo: str,
    area: str,
    subarea: Optional[str] = None,
    auth: tuple = Depends(usuario_actual),
):
    nombre_usuario, datos = auth
    tematica, subtematica = _resolver_ids_area(datos["id"], area, subarea)

    documento = _obtener_documento_activo(
        datos["id"],
        nombre_archivo,
        tematica["id"],
        subtematica["id"] if subtematica else None,
    )
    if not documento:
        raise HTTPException(404, "Documento no encontrado.")

    marcar_documento_eliminando(documento["id"])

    eliminado_de: list[str] = []
    nodos = obtener_nodos_documento(documento["id"])
    for nodo in nodos:
        ruta = nodo.get("ruta_fisica")
        if ruta and os.path.exists(ruta):
            os.remove(ruta)
            eliminado_de.append(nodo.get("nodo", "desconocido"))
            marcar_nodo_inactivo(documento["id"], nodo.get("nodo", ""))

    if not eliminado_de:
        ruta_sub = subarea if subarea else ""
        for nodo in NODOS:
            ruta = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, ruta_sub, nombre_archivo)
            if os.path.exists(ruta):
                os.remove(ruta)
                eliminado_de.append(nodo)
                marcar_nodo_inactivo(documento["id"], nodo)

    if not eliminado_de:
        raise HTTPException(404, "Archivo no encontrado en ningun nodo.")

    marcar_documento_eliminado(documento["id"])
    return {"mensaje": f"Archivo '{nombre_archivo}' eliminado de {eliminado_de}."}


@router.get("/admin/users", tags=["admin"])
def listar_usuarios(auth: tuple = Depends(obtener_admin)):
    _ = auth
    usuarios = db.table("usuarios").select("id, username, rol_id, activo").execute().data or []

    respuesta = {}
    for usuario in usuarios:
        rol = _rol_nombre_por_id(usuario["rol_id"])
        areas = [a["nombre"] for a in obtener_tematicas_usuario(usuario["id"])]
        respuesta[usuario["username"]] = {
            "rol": rol,
            "activo": usuario.get("activo", True),
            "areas": areas,
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


@router.delete("/admin/areas/{nombre_usuario}/{area}", tags=["admin"])
def admin_eliminar_area(
    nombre_usuario: str,
    area: str,
    auth: tuple = Depends(obtener_admin),
):
    _ = auth

    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")

    if area == "General":
        raise HTTPException(400, "No se puede eliminar 'General'.")

    tematica, _ = _resolver_ids_area(usuario["id"], area)
    general, _ = _resolver_ids_area(usuario["id"], "General")

    catalogo = _catalogo_areas_usuario(usuario["id"])
    docs = (
        db.table("documentos")
        .select("id, nombre_archivo, tematica_id, subtematica_id")
        .eq("usuario_id", usuario["id"])
        .eq("tematica_id", tematica["id"])
        .eq("estado", "activo")
        .execute()
        .data
        or []
    )

    for doc in docs:
        sub_nombre = ""
        if doc.get("subtematica_id"):
            sub_obj = catalogo["subtematicas_por_id"].get(doc["subtematica_id"])
            sub_nombre = sub_obj["nombre"] if sub_obj else ""

        for nodo in NODOS:
            ruta_origen = os.path.join(
                BASE_ALMACENAMIENTO,
                nodo,
                nombre_usuario,
                area,
                sub_nombre,
                doc["nombre_archivo"],
            )
            ruta_dest_dir = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, "General")
            os.makedirs(ruta_dest_dir, exist_ok=True)
            if os.path.exists(ruta_origen):
                shutil.move(ruta_origen, os.path.join(ruta_dest_dir, doc["nombre_archivo"]))

        db.table("documentos").update(
            {
                "tematica_id": general["id"],
                "subtematica_id": None,
            }
        ).eq("id", doc["id"]).execute()

    db.table("tematicas").delete().eq("id", tematica["id"]).execute()
    return {"mensaje": f"Area '{area}' eliminada. Documentos movidos a 'General'."}


@router.delete("/admin/areas/{nombre_usuario}/{area}/{subarea}", tags=["admin"])
def admin_eliminar_subarea(
    nombre_usuario: str,
    area: str,
    subarea: str,
    auth: tuple = Depends(obtener_admin),
):
    _ = auth

    usuario = obtener_usuario_por_nombre(nombre_usuario)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")

    tematica, sub = _resolver_ids_area(usuario["id"], area, subarea)

    docs = (
        db.table("documentos")
        .select("id, nombre_archivo")
        .eq("usuario_id", usuario["id"])
        .eq("subtematica_id", sub["id"])
        .eq("estado", "activo")
        .execute()
        .data
        or []
    )

    for doc in docs:
        for nodo in NODOS:
            ruta_origen = os.path.join(
                BASE_ALMACENAMIENTO,
                nodo,
                nombre_usuario,
                area,
                subarea,
                doc["nombre_archivo"],
            )
            ruta_dest_dir = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area)
            os.makedirs(ruta_dest_dir, exist_ok=True)
            if os.path.exists(ruta_origen):
                shutil.move(ruta_origen, os.path.join(ruta_dest_dir, doc["nombre_archivo"]))

        db.table("documentos").update({"subtematica_id": None}).eq("id", doc["id"]).execute()

    db.table("subtematicas").delete().eq("id", sub["id"]).execute()
    return {"mensaje": f"Subarea '{subarea}' eliminada. Documentos movidos a '{area}'."}

@router.put("/admin/users/{nombre_usuario}/estado", tags=["admin"])
def admin_cambiar_estado_usuario(
    nombre_usuario: str,
    activo: bool,
    auth: tuple = Depends(obtener_admin),
):
    admin_user, _ = auth

    if nombre_usuario == admin_user:
        raise HTTPException(400, "No puedes desactivar tu propia cuenta.")

    usuario = obtener_usuario_por_nombre(nombre_usuario)

    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")

    db.table("usuarios").update({
        "activo": activo
    }).eq("id", usuario["id"]).execute()

    estado = "activado" if activo else "desactivado"

    return {
        "mensaje": f"Usuario {estado} correctamente."
    }