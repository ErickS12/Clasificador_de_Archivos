"""
master/routes.py
=================
Router con todos los endpoints del maestro.
Se importa en worker/main.py para que cualquier nodo
pueda activar estas rutas cuando gane la elección de líder.

En master/main.py se usa así:
    from .routes import router
    app.include_router(router)

En worker/main.py se usa así:
    from master.routes import router as router_maestro
    app.include_router(router_maestro)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import FileResponse
import shutil, os, json
from typing import Optional

from master.auth     import (hashear_contrasena, verificar_contrasena, generar_token,
                              obtener_usuario_del_token, requiere_admin)
from master.gateway  import validar_carga
from master.consensus import clasificar_con_consenso
from master.adapter  import (adaptar_respuesta_carga, adaptar_respuesta_archivos,
                              resolver_area, construir_areas_planas)

router = APIRouter()

NODOS               = ["node1", "node2", "node3"]
BASE_ALMACENAMIENTO = "../storage/"
RUTA_METADATOS      = "../metadata/users/"
ARCHIVO_USUARIOS    = "../metadata/users.json"


# ══════════════════════════════════════════════════════════════════════════
# Helpers de persistencia
# ══════════════════════════════════════════════════════════════════════════

def cargar_usuarios() -> dict:
    with open(ARCHIVO_USUARIOS, "r") as f:
        return json.load(f)

def guardar_usuarios(datos: dict):
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump(datos, f, indent=4)

def cargar_metadatos(usuario: str) -> dict:
    ruta = os.path.join(RUTA_METADATOS, f"{usuario}.json")
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            return json.load(f)
    return {"files": []}

def guardar_metadatos(usuario: str, datos: dict):
    ruta = os.path.join(RUTA_METADATOS, f"{usuario}.json")
    with open(ruta, "w") as f:
        json.dump(datos, f, indent=4)


# ── Dependencia reutilizable ──────────────────────────────────────────────

def usuario_actual(autorizacion: str = Header(...)) -> tuple[str, dict]:
    if not autorizacion.startswith("Bearer "):
        raise HTTPException(401, "Se requiere Authorization: Bearer <token>")
    token = autorizacion[7:]
    usuarios = cargar_usuarios()
    return obtener_usuario_del_token(token, usuarios)

def obtener_admin(auth: tuple = Depends(usuario_actual)) -> tuple[str, dict]:
    nombre_usuario, datos = auth
    requiere_admin(datos)
    return nombre_usuario, datos


# ══════════════════════════════════════════════════════════════════════════
# 1. AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════════════

@router.post("/register", tags=["auth"])
def registrar(nombre_usuario: str, contrasena: str):
    usuarios = cargar_usuarios()
    if nombre_usuario in usuarios:
        raise HTTPException(400, "El nombre de usuario ya existe.")
    if len(contrasena) < 6:
        raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")
    rol = "admin" if not usuarios else "user"
    usuarios[nombre_usuario] = {
        "password_hash": hashear_contrasena(contrasena),
        "role":          rol,
        "session_token": None,
        "areas":         {"General": []}
    }
    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario '{nombre_usuario}' registrado.", "rol": rol}


@router.post("/login", tags=["auth"])
def iniciar_sesion(nombre_usuario: str, contrasena: str):
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    if not verificar_contrasena(contrasena, usuarios[nombre_usuario]["password_hash"]):
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    token = generar_token()
    usuarios[nombre_usuario]["session_token"] = token
    guardar_usuarios(usuarios)
    return {"mensaje": "Sesión iniciada.", "token": token, "rol": usuarios[nombre_usuario]["role"]}


@router.post("/logout", tags=["auth"])
def cerrar_sesion(auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    usuarios = cargar_usuarios()
    usuarios[nombre_usuario]["session_token"] = None
    guardar_usuarios(usuarios)
    return {"mensaje": "Sesión cerrada."}


# ══════════════════════════════════════════════════════════════════════════
# 2. ÁREAS
# ══════════════════════════════════════════════════════════════════════════

@router.get("/categories", tags=["areas"])
def obtener_categorias(auth: tuple = Depends(usuario_actual)):
    nombre_usuario, datos = auth
    return {"areas": datos["areas"]}


@router.post("/areas", tags=["areas"])
def crear_area(area: str, auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    usuarios = cargar_usuarios()
    if area == "General":
        raise HTTPException(400, "'General' es un área reservada del sistema.")
    if area in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(400, f"El área '{area}' ya existe.")
    usuarios[nombre_usuario]["areas"][area] = []
    guardar_usuarios(usuarios)
    return {"mensaje": f"Área '{area}' creada."}


@router.post("/areas/{area}/sub", tags=["areas"])
def crear_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    usuarios = cargar_usuarios()
    areas_usuario = usuarios[nombre_usuario]["areas"]
    if area not in areas_usuario:
        raise HTTPException(404, f"El área '{area}' no existe.")
    if subarea in areas_usuario[area]:
        raise HTTPException(400, f"La subárea '{subarea}' ya existe en '{area}'.")
    areas_usuario[area].append(subarea)
    guardar_usuarios(usuarios)
    return {"mensaje": f"Subárea '{subarea}' creada en '{area}'."}


@router.delete("/areas/{area}", tags=["areas"])
def eliminar_area(area: str, auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    usuarios  = cargar_usuarios()
    metadatos = cargar_metadatos(nombre_usuario)
    if area == "General":
        raise HTTPException(400, "No se puede eliminar el área 'General'.")
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe.")
    if any(f["area"] == area for f in metadatos["files"]):
        raise HTTPException(400, f"El área '{area}' contiene documentos. Elimínalos primero.")
    del usuarios[nombre_usuario]["areas"][area]
    guardar_usuarios(usuarios)
    return {"mensaje": f"Área '{area}' eliminada."}


@router.delete("/areas/{area}/sub/{subarea}", tags=["areas"])
def eliminar_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    usuarios  = cargar_usuarios()
    metadatos = cargar_metadatos(nombre_usuario)
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe.")
    if subarea not in usuarios[nombre_usuario]["areas"][area]:
        raise HTTPException(404, f"La subárea '{subarea}' no existe en '{area}'.")
    if any(f["area"] == area and f.get("subarea") == subarea for f in metadatos["files"]):
        raise HTTPException(400, f"La subárea '{subarea}' contiene documentos. Elimínalos primero.")
    usuarios[nombre_usuario]["areas"][area].remove(subarea)
    guardar_usuarios(usuarios)
    return {"mensaje": f"Subárea '{subarea}' eliminada de '{area}'."}


# ══════════════════════════════════════════════════════════════════════════
# 3. DOCUMENTOS
# ══════════════════════════════════════════════════════════════════════════

@router.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...),
                         auth: tuple = Depends(usuario_actual)):
    nombre_usuario, datos_usuario = auth
    validar_carga(archivo)
    areas_usuario = datos_usuario["areas"]
    areas_planas  = construir_areas_planas(areas_usuario)

    ruta_temporal = f"temp_{nombre_usuario}_{archivo.filename}"
    with open(ruta_temporal, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    try:
        predicho, votos = clasificar_con_consenso(ruta_temporal, areas_planas)
        area, subarea   = resolver_area(predicho, areas_usuario)

        nodos_almacenados = []
        for nodo in NODOS:
            directorio_destino = os.path.join(
                BASE_ALMACENAMIENTO, nodo, nombre_usuario, area,
                subarea if subarea else ""
            )
            os.makedirs(directorio_destino, exist_ok=True)
            shutil.copy(ruta_temporal, os.path.join(directorio_destino, archivo.filename))
            nodos_almacenados.append(nodo)
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

    metadatos = cargar_metadatos(nombre_usuario)
    metadatos["files"].append({
        "name":    archivo.filename,
        "area":    area,
        "subarea": subarea,
        "nodes":   nodos_almacenados,
        "votos":   votos,
        "version": 1
    })
    guardar_metadatos(nombre_usuario, metadatos)
    return adaptar_respuesta_carga(archivo.filename, area, subarea, nodos_almacenados, votos)


@router.get("/files", tags=["documentos"])
def obtener_archivos(auth: tuple = Depends(usuario_actual)):
    nombre_usuario, datos_usuario = auth
    areas_usuario = datos_usuario["areas"]
    metadatos     = cargar_metadatos(nombre_usuario)

    arbol = {}
    for area, subareas in areas_usuario.items():
        arbol[area] = {"files": []}
        for sub in subareas:
            arbol[area][sub] = {"files": []}

    for f in metadatos["files"]:
        area    = f["area"]
        subarea = f.get("subarea", "")
        nombre  = f["name"]
        arbol.setdefault(area, {"files": []})
        if subarea:
            arbol[area].setdefault(subarea, {"files": []})
            arbol[area][subarea]["files"].append(nombre)
        else:
            arbol[area]["files"].append(nombre)

    return adaptar_respuesta_archivos(nombre_usuario, arbol)


@router.get("/download", tags=["documentos"])
def descargar_archivo(nombre_archivo: str = Query(...),
                      area: str = Query(...),
                      subarea: Optional[str] = Query(None),
                      auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    ruta_sub = subarea if subarea else ""
    for nodo in NODOS:
        ruta = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, ruta_sub, nombre_archivo)
        if os.path.exists(ruta):
            return FileResponse(ruta, media_type="application/pdf", filename=nombre_archivo)
    raise HTTPException(404, "Archivo no encontrado en ningún nodo.")


@router.delete("/document", tags=["documentos"])
def eliminar_documento(nombre_archivo: str, area: str,
                       subarea: Optional[str] = None,
                       auth: tuple = Depends(usuario_actual)):
    nombre_usuario, _ = auth
    ruta_sub = subarea if subarea else ""
    eliminado_de = []
    for nodo in NODOS:
        ruta = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, ruta_sub, nombre_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
            eliminado_de.append(nodo)
    if not eliminado_de:
        raise HTTPException(404, "Archivo no encontrado en ningún nodo.")
    metadatos = cargar_metadatos(nombre_usuario)
    metadatos["files"] = [
        f for f in metadatos["files"]
        if not (f["name"] == nombre_archivo and f["area"] == area
                and f.get("subarea", "") == (subarea or ""))
    ]
    guardar_metadatos(nombre_usuario, metadatos)
    return {"mensaje": f"Archivo '{nombre_archivo}' eliminado de {eliminado_de}."}


# ══════════════════════════════════════════════════════════════════════════
# 4. ADMINISTRADOR
# ══════════════════════════════════════════════════════════════════════════

@router.get("/admin/users", tags=["admin"])
def listar_usuarios(auth: tuple = Depends(obtener_admin)):
    usuarios = cargar_usuarios()
    return {
        u: {"rol": d["role"], "areas": list(d["areas"].keys())}
        for u, d in usuarios.items()
    }


@router.post("/admin/users", tags=["admin"])
def admin_crear_usuario(nombre_usuario: str, contrasena: str,
                        rol: str = "user",
                        auth: tuple = Depends(obtener_admin)):
    if rol not in ("user", "admin"):
        raise HTTPException(400, "Rol inválido. Usa 'user' o 'admin'.")
    usuarios = cargar_usuarios()
    if nombre_usuario in usuarios:
        raise HTTPException(400, "El nombre de usuario ya existe.")
    usuarios[nombre_usuario] = {
        "password_hash": hashear_contrasena(contrasena),
        "role":          rol,
        "session_token": None,
        "areas":         {"General": []}
    }
    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario '{nombre_usuario}' creado con rol '{rol}'."}


@router.delete("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_eliminar_usuario(nombre_usuario: str, auth: tuple = Depends(obtener_admin)):
    usuario_admin, _ = auth
    if nombre_usuario == usuario_admin:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta.")
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")
    for nodo in NODOS:
        dir_usuario = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario)
        if os.path.exists(dir_usuario):
            shutil.rmtree(dir_usuario)
    archivo_meta = os.path.join(RUTA_METADATOS, f"{nombre_usuario}.json")
    if os.path.exists(archivo_meta):
        os.remove(archivo_meta)
    del usuarios[nombre_usuario]
    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario '{nombre_usuario}' eliminado."}


@router.put("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_actualizar_usuario(nombre_usuario: str,
                             nuevo_nombre_usuario: Optional[str] = None,
                             nueva_contrasena: Optional[str] = None,
                             nuevo_rol: Optional[str] = None,
                             auth: tuple = Depends(obtener_admin)):
    if not nuevo_nombre_usuario and not nueva_contrasena and not nuevo_rol:
        raise HTTPException(400, "Debes proporcionar al menos un campo a actualizar.")
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")
    if nuevo_nombre_usuario and nuevo_nombre_usuario != nombre_usuario:
        if nuevo_nombre_usuario in usuarios:
            raise HTTPException(400, "El nuevo nombre de usuario ya existe.")
        usuarios[nuevo_nombre_usuario] = usuarios.pop(nombre_usuario)
        for nodo in NODOS:
            dir_antiguo = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario)
            dir_nuevo   = os.path.join(BASE_ALMACENAMIENTO, nodo, nuevo_nombre_usuario)
            if os.path.exists(dir_antiguo):
                os.rename(dir_antiguo, dir_nuevo)
        meta_antiguo = os.path.join(RUTA_METADATOS, f"{nombre_usuario}.json")
        meta_nuevo   = os.path.join(RUTA_METADATOS, f"{nuevo_nombre_usuario}.json")
        if os.path.exists(meta_antiguo):
            os.rename(meta_antiguo, meta_nuevo)
        nombre_usuario = nuevo_nombre_usuario
    if nueva_contrasena:
        if len(nueva_contrasena) < 6:
            raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")
        usuarios[nombre_usuario]["password_hash"] = hashear_contrasena(nueva_contrasena)
        usuarios[nombre_usuario]["session_token"] = None
    if nuevo_rol:
        if nuevo_rol not in ("user", "admin"):
            raise HTTPException(400, "Rol inválido. Usa 'user' o 'admin'.")
        usuarios[nombre_usuario]["role"] = nuevo_rol
    guardar_usuarios(usuarios)
    return {"mensaje": "Usuario actualizado correctamente.", "nombre_usuario": nombre_usuario}


@router.delete("/admin/areas/{nombre_usuario}/{area}", tags=["admin"])
def admin_eliminar_area(nombre_usuario: str, area: str,
                        auth: tuple = Depends(obtener_admin)):
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")
    if area == "General":
        raise HTTPException(400, "No se puede eliminar 'General'.")
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe para '{nombre_usuario}'.")
    metadatos = cargar_metadatos(nombre_usuario)
    for f in metadatos["files"]:
        if f["area"] == area:
            subarea_antiguo = f.get("subarea", "")
            for nodo in NODOS:
                ruta_antigua = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario,
                                            area, subarea_antiguo, f["name"])
                dir_nuevo    = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, "General")
                os.makedirs(dir_nuevo, exist_ok=True)
                if os.path.exists(ruta_antigua):
                    shutil.move(ruta_antigua, os.path.join(dir_nuevo, f["name"]))
            f["area"]    = "General"
            f["subarea"] = ""
    guardar_metadatos(nombre_usuario, metadatos)
    del usuarios[nombre_usuario]["areas"][area]
    guardar_usuarios(usuarios)
    return {"mensaje": f"Área '{area}' eliminada. Documentos movidos a 'General'."}


@router.delete("/admin/areas/{nombre_usuario}/{area}/{subarea}", tags=["admin"])
def admin_eliminar_subarea(nombre_usuario: str, area: str, subarea: str,
                           auth: tuple = Depends(obtener_admin)):
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe para '{nombre_usuario}'.")
    if subarea not in usuarios[nombre_usuario]["areas"][area]:
        raise HTTPException(404, f"La subárea '{subarea}' no existe en '{area}'.")
    metadatos = cargar_metadatos(nombre_usuario)
    for f in metadatos["files"]:
        if f["area"] == area and f.get("subarea") == subarea:
            for nodo in NODOS:
                ruta_antigua = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario,
                                            area, subarea, f["name"])
                dir_nuevo    = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area)
                os.makedirs(dir_nuevo, exist_ok=True)
                if os.path.exists(ruta_antigua):
                    shutil.move(ruta_antigua, os.path.join(dir_nuevo, f["name"]))
            f["subarea"] = ""
    guardar_metadatos(nombre_usuario, metadatos)
    usuarios[nombre_usuario]["areas"][area].remove(subarea)
    guardar_usuarios(usuarios)
    return {"mensaje": f"Subárea '{subarea}' eliminada. Documentos movidos a '{area}'."}
