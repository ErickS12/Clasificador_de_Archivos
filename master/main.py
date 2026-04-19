"""
Nodo Maestro — API Principal
=============================
Endpoints organizados en cuatro bloques:

  1. Autenticación  — /register, /login, /logout
  2. Áreas          — /areas  (temáticas y subtemáticas, 2 niveles)
  3. Documentos     — /upload, /files, /download, /document
  4. Admin          — /admin/*  (solo rol administrador)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil, os, json
from typing import Optional

from .auth      import (hashear_contraseña, verificar_contraseña, generar_token,
                        obtener_usuario_del_token, requiere_admin)
from .gateway   import LoggingMiddleware, validar_carga
from .consensus import clasificar_con_consenso
from .adapter   import (adaptar_respuesta_carga, adaptar_respuesta_archivos,
                        resolver_area, construir_áreas_planas)

app = FastAPI(title="Clasificador Distribuido de Archivos Científicos")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.add_middleware(LoggingMiddleware)

# ── Rutas ──────────────────────────────────────────────────────────────────
NODOS         = ["node1", "node2", "node3"]
BASE_ALMACENAMIENTO  = "../storage/"
RUTA_METADATOS = "../metadata/users/"
ARCHIVO_USUARIOS    = "../metadata/users.json"

for nodo in NODOS:
    os.makedirs(os.path.join(BASE_ALMACENAMIENTO, nodo), exist_ok=True)
os.makedirs(RUTA_METADATOS, exist_ok=True)

if not os.path.exists(ARCHIVO_USUARIOS):
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump({}, f, indent=4)


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


# ── Dependencia reutilizable: extrae y valida el token ────────────────────

def usuario_actual(autorizacion: str = Header(...)) -> tuple[str, dict]:
    if not autorizacion.startswith("Bearer "):
        raise HTTPException(401, "Se requiere Authorization: Bearer <token>")
    token = autorizacion[7:]
    usuarios = cargar_usuarios()
    return obtener_usuario_del_token(token, usuarios)


# ══════════════════════════════════════════════════════════════════════════
# 1. AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════════════

@app.post("/register", tags=["auth"])
def registrar(nombre_usuario: str, contraseña: str):
    """
    Registra un nuevo usuario.
    El primer usuario registrado recibe rol de administrador automáticamente.
    'General' siempre se agrega como área por defecto.
    """
    usuarios = cargar_usuarios()

    if nombre_usuario in usuarios:
        raise HTTPException(400, "El nombre de usuario ya existe.")
    if len(contraseña) < 6:
        raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")

    rol = "admin" if not usuarios else "user"

    usuarios[nombre_usuario] = {
        "password_hash":  hashear_contraseña(contraseña),
        "role":           rol,
        "session_token":  None,
        "areas":          {"General": []}
    }
    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario '{nombre_usuario}' registrado.", "rol": rol}


@app.post("/login", tags=["auth"])
def iniciar_sesion(nombre_usuario: str, contraseña: str):
    """
    Inicia sesión. Devuelve un token de sesión que debe enviarse
    en el header Authorization: Bearer <token> en cada request.
    """
    usuarios = cargar_usuarios()

    if nombre_usuario not in usuarios:
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    if not verificar_contraseña(contraseña, usuarios[nombre_usuario]["password_hash"]):
        raise HTTPException(401, "Usuario o contraseña incorrectos.")

    token = generar_token()
    usuarios[nombre_usuario]["session_token"] = token
    guardar_usuarios(usuarios)

    return {
        "mensaje": "Sesión iniciada.",
        "token":   token,
        "rol":     usuarios[nombre_usuario]["role"]
    }


@app.post("/logout", tags=["auth"])
def cerrar_sesion(auth: tuple = Depends(usuario_actual)):
    """Cierra la sesión invalidando el token."""
    nombre_usuario, _ = auth
    usuarios = cargar_usuarios()
    usuarios[nombre_usuario]["session_token"] = None
    guardar_usuarios(usuarios)
    return {"mensaje": "Sesión cerrada."}


# ══════════════════════════════════════════════════════════════════════════
# 2. ÁREAS (temáticas y subtemáticas — 2 niveles)
# ══════════════════════════════════════════════════════════════════════════

@app.get("/categories", tags=["areas"])
def obtener_categorías(auth: tuple = Depends(usuario_actual)):
    """Devuelve la jerarquía completa de áreas del usuario."""
    nombre_usuario, datos = auth
    return {"areas": datos["areas"]}


@app.post("/areas", tags=["areas"])
def crear_area(area: str, auth: tuple = Depends(usuario_actual)):
    """
    Crea una nueva temática de primer nivel.
    'General' siempre existe y no puede crearse manualmente.
    """
    nombre_usuario, _ = auth
    usuarios = cargar_usuarios()

    if area == "General":
        raise HTTPException(400, "'General' es un área reservada del sistema.")
    if area in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(400, f"El área '{area}' ya existe.")

    usuarios[nombre_usuario]["areas"][area] = []
    guardar_usuarios(usuarios)
    return {"mensaje": f"Área '{area}' creada."}


@app.post("/areas/{area}/sub", tags=["areas"])
def crear_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    """Crea una subatemática dentro de una temática existente."""
    nombre_usuario, _ = auth
    usuarios = cargar_usuarios()
    áreas_usuario = usuarios[nombre_usuario]["areas"]

    if area not in áreas_usuario:
        raise HTTPException(404, f"El área '{area}' no existe.")
    if subarea in áreas_usuario[area]:
        raise HTTPException(400, f"La subárea '{subarea}' ya existe en '{area}'.")

    áreas_usuario[area].append(subarea)
    guardar_usuarios(usuarios)
    return {"mensaje": f"Subárea '{subarea}' creada en '{area}'."}


@app.delete("/areas/{area}", tags=["areas"])
def eliminar_area(area: str, auth: tuple = Depends(usuario_actual)):
    """
    Elimina una temática. Solo si está vacía (sin documentos ni subáreas con documentos).
    Los administradores pueden usar /admin/areas/{user}/{area} para borrar aunque no esté vacía.
    """
    nombre_usuario, _ = auth
    usuarios    = cargar_usuarios()
    metadatos = cargar_metadatos(nombre_usuario)

    if area == "General":
        raise HTTPException(400, "No se puede eliminar el área 'General'.")
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe.")

    # Verificar que no tenga documentos
    docs_en_area = [f for f in metadatos["files"]
                    if f["area"] == area]
    if docs_en_area:
        raise HTTPException(400, f"El área '{area}' contiene documentos. Elimínalos primero.")

    del usuarios[nombre_usuario]["areas"][area]
    guardar_usuarios(usuarios)
    return {"mensaje": f"Área '{area}' eliminada."}


@app.delete("/areas/{area}/sub/{subarea}", tags=["areas"])
def eliminar_subarea(area: str, subarea: str, auth: tuple = Depends(usuario_actual)):
    """
    Elimina una subtemática. Solo si no tiene documentos asociados.
    """
    nombre_usuario, _ = auth
    usuarios    = cargar_usuarios()
    metadatos = cargar_metadatos(nombre_usuario)

    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe.")
    if subarea not in usuarios[nombre_usuario]["areas"][area]:
        raise HTTPException(404, f"La subárea '{subarea}' no existe en '{area}'.")

    docs_en_subarea = [f for f in metadatos["files"]
                       if f["area"] == area and f.get("subarea") == subarea]
    if docs_en_subarea:
        raise HTTPException(400, f"La subárea '{subarea}' contiene documentos. Elimínalos primero.")

    usuarios[nombre_usuario]["areas"][area].remove(subarea)
    guardar_usuarios(usuarios)
    return {"mensaje": f"Subárea '{subarea}' eliminada de '{area}'."}


# ══════════════════════════════════════════════════════════════════════════
# 3. DOCUMENTOS
# ══════════════════════════════════════════════════════════════════════════

@app.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...),
                      auth: tuple = Depends(usuario_actual)):
    """
    Sube un PDF, lo clasifica por consenso y lo replica en los 3 nodos.

    Flujo:
      1. Gateway valida el archivo
      2. Consenso clasifica con mayoría de votos
      3. Adapter resuelve área/subárea en la jerarquía del usuario
      4. Se replica en node1, node2, node3
      5. Se guarda en metadatos
    """
    nombre_usuario, datos_usuario = auth
    validar_carga(archivo)

    áreas_usuario  = datos_usuario["areas"]
    áreas_planas  = construir_áreas_planas(áreas_usuario)

    ruta_temporal = f"temp_{nombre_usuario}_{archivo.filename}"
    with open(ruta_temporal, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)

    try:
        predicho, votos  = clasificar_con_consenso(ruta_temporal, áreas_planas)
        area, subarea     = resolver_area(predicho, áreas_usuario)

        nodos_almacenados = []
        for nodo in NODOS:
            directorio_destino = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area,
                                    subarea if subarea else "")
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


@app.get("/files", tags=["documentos"])
def obtener_archivos(auth: tuple = Depends(usuario_actual)):
    """
    Devuelve el árbol de clasificación de dos niveles del usuario.

    Ejemplo de respuesta:
    {
      "Redes": {
        "files": ["paper1.pdf"],
        "Protocolos": {"files": ["paper2.pdf"]},
        "Topologías":  {"files": []}
      },
      "General": {"files": ["paper3.pdf"]}
    }
    """
    nombre_usuario, datos_usuario = auth
    áreas_usuario = datos_usuario["areas"]
    metadatos   = cargar_metadatos(nombre_usuario)

    # Inicializar árbol con todas las áreas (aunque vacías)
    arbol = {}
    for area, subareas in áreas_usuario.items():
        arbol[area] = {"files": []}
        for sub in subareas:
            arbol[area][sub] = {"files": []}

    for f in metadatos["files"]:
        area    = f["area"]
        subarea = f.get("subarea", "")
        nombre    = f["name"]

        arbol.setdefault(area, {"files": []})

        if subarea:
            arbol[area].setdefault(subarea, {"files": []})
            arbol[area][subarea]["files"].append(nombre)
        else:
            arbol[area]["files"].append(nombre)

    return adaptar_respuesta_archivos(nombre_usuario, arbol)


@app.get("/download", tags=["documentos"])
def descargar_archivo(nombre_archivo: str, area: str,
                  subarea: Optional[str] = None,
                  auth: tuple = Depends(usuario_actual)):
    """
    Descarga un archivo intentando node1 → node2 → node3.
    Tolerancia a fallos: si un nodo está caído prueba el siguiente.
    """
    nombre_usuario, _ = auth
    ruta_sub = subarea if subarea else ""

    for nodo in NODOS:
        ruta = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, ruta_sub, nombre_archivo)
        if os.path.exists(ruta):
            return FileResponse(ruta, media_type="application/pdf", filename=nombre_archivo)

    raise HTTPException(404, "Archivo no encontrado en ningún nodo.")


@app.delete("/document", tags=["documentos"])
def eliminar_documento(nombre_archivo: str, area: str,
                    subarea: Optional[str] = None,
                    auth: tuple = Depends(usuario_actual)):
    """
    Elimina un documento de los 3 nodos y de los metadatos del usuario.
    """
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

    # Quitar de metadatos
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

def obtener_admin(auth: tuple = Depends(usuario_actual)) -> tuple[str, dict]:
    nombre_usuario, datos = auth
    requiere_admin(datos)
    return nombre_usuario, datos


@app.get("/admin/users", tags=["admin"])
def listar_usuarios(auth: tuple = Depends(obtener_admin)):
    """Lista todos los usuarios con su rol (sin mostrar hashes ni tokens)."""
    usuarios = cargar_usuarios()
    return {
        u: {"rol": d["role"], "areas": list(d["areas"].keys())}
        for u, d in usuarios.items()
    }


@app.post("/admin/users", tags=["admin"])
def admin_crear_usuario(nombre_usuario: str, contraseña: str,
                       rol: str = "user",
                       auth: tuple = Depends(obtener_admin)):
    """
    Crea un usuario (el admin puede asignar rol).
    Roles válidos: 'user', 'admin'.
    """
    if rol not in ("user", "admin"):
        raise HTTPException(400, "Rol inválido. Usa 'user' o 'admin'.")

    usuarios = cargar_usuarios()
    if nombre_usuario in usuarios:
        raise HTTPException(400, "El nombre de usuario ya existe.")

    usuarios[nombre_usuario] = {
        "password_hash": hashear_contraseña(contraseña),
        "role":          rol,
        "session_token": None,
        "areas":         {"General": []}
    }
    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario '{nombre_usuario}' creado con rol '{rol}'."}


@app.delete("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_eliminar_usuario(nombre_usuario: str, auth: tuple = Depends(obtener_admin)):
    """
    Elimina un usuario y todos sus archivos en los 3 nodos.
    No se puede eliminar a uno mismo.
    """
    usuario_admin, _ = auth
    if nombre_usuario == usuario_admin:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta.")

    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")

    # Eliminar archivos físicos
    for nodo in NODOS:
        directorio_usuario = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario)
        if os.path.exists(directorio_usuario):
            shutil.rmtree(directorio_usuario)

    # Eliminar metadatos
    archivo_meta = os.path.join(RUTA_METADATOS, f"{nombre_usuario}.json")
    if os.path.exists(archivo_meta):
        os.remove(archivo_meta)

    del usuarios[nombre_usuario]
    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario '{nombre_usuario}' eliminado."}


@app.put("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_actualizar_usuario(nombre_usuario: str,
                       nuevo_nombre_usuario: Optional[str] = None,
                       nueva_contraseña: Optional[str] = None,
                       auth: tuple = Depends(obtener_admin)):
    """
    Modifica el nombre de usuario y/o contraseña de cualquier cuenta.
    Al menos uno de los dos parámetros debe enviarse.
    """
    if not nuevo_nombre_usuario and not nueva_contraseña:
        raise HTTPException(400, "Debes proporcionar nuevo nombre de usuario y/o nueva contraseña.")

    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")

    if nuevo_nombre_usuario and nuevo_nombre_usuario != nombre_usuario:
        if nuevo_nombre_usuario in usuarios:
            raise HTTPException(400, "El nuevo nombre de usuario ya existe.")

        # Renombrar en users.json
        usuarios[nuevo_nombre_usuario] = usuarios.pop(nombre_usuario)

        # Renombrar archivos físicos en los 3 nodos
        for nodo in NODOS:
            directorio_antiguo = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario)
            directorio_nuevo = os.path.join(BASE_ALMACENAMIENTO, nodo, nuevo_nombre_usuario)
            if os.path.exists(directorio_antiguo):
                os.rename(directorio_antiguo, directorio_nuevo)

        # Renombrar metadatos
        metadatos_antiguo = os.path.join(RUTA_METADATOS, f"{nombre_usuario}.json")
        metadatos_nuevo = os.path.join(RUTA_METADATOS, f"{nuevo_nombre_usuario}.json")
        if os.path.exists(metadatos_antiguo):
            os.rename(metadatos_antiguo, metadatos_nuevo)

        nombre_usuario = nuevo_nombre_usuario

    if nueva_contraseña:
        if len(nueva_contraseña) < 6:
            raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")
        usuarios[nombre_usuario]["password_hash"] = hashear_contraseña(nueva_contraseña)
        usuarios[nombre_usuario]["session_token"] = None  # forzar re-login

    guardar_usuarios(usuarios)
    return {"mensaje": f"Usuario actualizado correctamente.", "nombre_usuario": nombre_usuario}


@app.delete("/admin/areas/{nombre_usuario}/{area}", tags=["admin"])
def admin_eliminar_area(nombre_usuario: str, area: str,
                       auth: tuple = Depends(obtener_admin)):
    """
    Elimina una temática de cualquier usuario AUNQUE NO ESTÉ VACÍA.
    Los documentos dentro se mueven a 'General'.
    """
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")
    if area == "General":
        raise HTTPException(400, "No se puede eliminar 'General'.")
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe para '{nombre_usuario}'.")

    metadatos = cargar_metadatos(nombre_usuario)

    # Mover archivos del área a General en metadatos y en storage
    for f in metadatos["files"]:
        if f["area"] == area:
            subarea_antiguo  = f.get("subarea", "")
            for nodo in NODOS:
                ruta_antigua = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area,
                                         subarea_antiguo, f["name"])
                directorio_nuevo  = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, "General")
                os.makedirs(directorio_nuevo, exist_ok=True)
                if os.path.exists(ruta_antigua):
                    shutil.move(ruta_antigua, os.path.join(directorio_nuevo, f["name"]))
            f["area"]    = "General"
            f["subarea"] = ""

    guardar_metadatos(nombre_usuario, metadatos)

    del usuarios[nombre_usuario]["areas"][area]
    guardar_usuarios(usuarios)
    return {"mensaje": f"Área '{area}' eliminada. Documentos movidos a 'General'."}


@app.delete("/admin/areas/{nombre_usuario}/{area}/{subarea}", tags=["admin"])
def admin_eliminar_subarea(nombre_usuario: str, area: str, subarea: str,
                          auth: tuple = Depends(obtener_admin)):
    """
    Elimina una subatemática de cualquier usuario AUNQUE NO ESTÉ VACÍA.
    Los documentos dentro se mueven al área padre.
    """
    usuarios = cargar_usuarios()
    if nombre_usuario not in usuarios:
        raise HTTPException(404, "Usuario no encontrado.")
    if area not in usuarios[nombre_usuario]["areas"]:
        raise HTTPException(404, f"El área '{area}' no existe para '{nombre_usuario}'.")
    if subarea not in usuarios[nombre_usuario]["areas"][area]:
        raise HTTPException(404, f"La subárea '{subarea}' no existe en '{area}'.")

    metadatos = cargar_metadatos(nombre_usuario)

    # Mover documentos de la subárea al área padre
    for f in metadatos["files"]:
        if f["area"] == area and f.get("subarea") == subarea:
            for nodo in NODOS:
                ruta_antigua = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area, subarea, f["name"])
                directorio_nuevo  = os.path.join(BASE_ALMACENAMIENTO, nodo, nombre_usuario, area)
                os.makedirs(directorio_nuevo, exist_ok=True)
                if os.path.exists(ruta_antigua):
                    shutil.move(ruta_antigua, os.path.join(directorio_nuevo, f["name"]))
            f["subarea"] = ""

    guardar_metadatos(nombre_usuario, metadatos)

    usuarios[nombre_usuario]["areas"][area].remove(subarea)
    guardar_usuarios(usuarios)
    return {"mensaje": f"Subárea '{subarea}' eliminada. Documentos movidos a '{area}'."}
