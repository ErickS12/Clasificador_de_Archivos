# 🔧 Documentación Técnica - Integración en main.py

## Tabla de Contenidos
1. [Importaciones y Setup](#importaciones-y-setup)
2. [Dependencias (Dependency Injection)](#dependencias-dependency-injection)
3. [Integración Auth](#integración-auth)
4. [Integración Gateway](#integración-gateway)
5. [Integración Consensus](#integración-consensus)
6. [Integración Adapter](#integración-adapter)
7. [Manejo de Errores](#manejo-de-errores)

---

## 📦 Importaciones y Setup

```python
# ═══════════════════════════════════════════════════════════════
# Importaciones en main.py
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
# ├─ FastAPI: Framework REST
# ├─ UploadFile: Manejo de uploads
# ├─ HTTPException: Errores HTTP estandarizados
# ├─ Header: Extrae headers HTTP
# └─ Depends: Inyección de dependencias

from fastapi.middleware.cors import CORSMiddleware
# └─ Permite CORS para frontend

from fastapi.responses import FileResponse
# └─ Descarga de archivos

import shutil, os, json
# ├─ shutil: Copiar/eliminar archivos
# ├─ os: Rutas del sistema de archivos
# └─ json: Serialización de datos

from .auth      import (hashear_contraseña, verificar_contraseña, generar_token,
                        obtener_usuario_del_token, requiere_admin)
# ├─ hashear_contraseña: Hash PBKDF2
# ├─ verificar_contraseña: Valida hash
# ├─ generar_token: Crea UUID
# ├─ obtener_usuario_del_token: Valida token
# └─ requiere_admin: Verifica rol

from .gateway   import LoggingMiddleware, validar_carga
# ├─ LoggingMiddleware: Middleware de logging
# └─ validar_carga: Valida PDF

from .consensus import clasificar_con_consenso
# └─ clasificar_con_consenso: Orquesta workers

from .adapter   import (adaptar_respuesta_carga, adaptar_respuesta_archivos,
                        resolver_area, construir_áreas_planas)
# ├─ adaptar_respuesta_carga: Formatea respuesta de upload
# ├─ adaptar_respuesta_archivos: Formatea árbol
# ├─ resolver_area: Mapea predicción a área
# └─ construir_áreas_planas: Prepara áreas para workers

# ═══════════════════════════════════════════════════════════════
# Creación de la app
# ═══════════════════════════════════════════════════════════════

app = FastAPI(title="Clasificador Distribuido de Archivos Científicos")

# ✓ Middleware 1: CORS
app.add_middleware(CORSMiddleware, 
                   allow_origins=["*"],
                   allow_methods=["*"], 
                   allow_headers=["*"])
# └─ Permite que cualquier origen acceda a los endpoints

# ✓ Middleware 2: Logging (de gateway.py)
app.add_middleware(LoggingMiddleware)
# └─ Registra tiempo y código HTTP de cada request

# ═══════════════════════════════════════════════════════════════
# Configuración de Rutas
# ═══════════════════════════════════════════════════════════════

NODOS = ["node1", "node2", "node3"]
# └─ Identificadores de workers (consensus.py los contacta)

BASE_ALMACENAMIENTO = "../storage/"
# └─ Ruta raíz para replicación en 3 nodos

RUTA_METADATOS = "../metadata/users/"
# └─ Donde se guardan los .json de cada usuario

ARCHIVO_USUARIOS = "../metadata/users.json"
# └─ Archivo JSON con todos los usuarios y contraseñas

# Inicializa directorios
for nodo in NODOS:
    os.makedirs(os.path.join(BASE_ALMACENAMIENTO, nodo), exist_ok=True)
os.makedirs(RUTA_METADATOS, exist_ok=True)

if not os.path.exists(ARCHIVO_USUARIOS):
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump({}, f, indent=4)
# └─ Si users.json no existe, lo crea vacío
```

---

## 🔌 Dependencias (Dependency Injection)

FastAPI usa el patrón **Dependency Injection** con `Depends()`. Esto permite:
- Validar usuarios en cada request
- Reutilizar código
- Inyectar dependencias automáticamente

### Ejemplo: usuario_actual()

```python
# ═══════════════════════════════════════════════════════════════
# DEPENDENCIA: usuario_actual()
# ═══════════════════════════════════════════════════════════════

def usuario_actual(autorizacion: str = Header(...)) -> tuple[str, dict]:
    """
    Dependencia reutilizable que:
    1. Extrae el token del header Authorization: Bearer <token>
    2. Lo valida usando auth.obtener_usuario_del_token()
    3. Devuelve (nombre_usuario, datos_usuario)
    
    Se usa con: Depends(usuario_actual) en cualquier endpoint
    """
    
    # ─────────────────────────────────────────────────────────
    # Paso 1: Extraer token del header
    # ─────────────────────────────────────────────────────────
    
    if not autorizacion.startswith("Bearer "):
        raise HTTPException(401, "Se requiere Authorization: Bearer <token>")
    
    token = autorizacion[7:]  # Quita "Bearer " (7 caracteres)
    # Ej: "Bearer abc123def" → "abc123def"
    
    # ─────────────────────────────────────────────────────────
    # Paso 2: Cargar usuarios y validar token (auth.py)
    # ─────────────────────────────────────────────────────────
    
    usuarios = cargar_usuarios()  # Lee users.json
    
    return obtener_usuario_del_token(token, usuarios)
    #      ↑ auth.py
    # Esta función:
    # ├─ Recorre todos los usuarios
    # ├─ Busca quién tiene ese session_token
    # ├─ Si encuentra: devuelve (nombre_usuario, datos)
    # └─ Si no: lanza HTTPException(401, "Token inválido")


# ═══════════════════════════════════════════════════════════════
# USO: En cualquier endpoint autenticado
# ═══════════════════════════════════════════════════════════════

@app.get("/files", tags=["documentos"])
def obtener_archivos(auth: tuple = Depends(usuario_actual)):
    #                         ↑ inyecta usuario_actual()
    
    nombre_usuario, datos_usuario = auth
    # Ahora tengo:
    # - nombre_usuario: "juan"
    # - datos_usuario: {"password_hash": "...", "role": "user", "areas": {...}}
    
    áreas_usuario = datos_usuario["areas"]
    # ├─ {"Redes": ["Protocolos", "Topologías"], "General": []}


# ═══════════════════════════════════════════════════════════════
# DEPENDENCIA DERIVADA: obtener_admin()
# ═══════════════════════════════════════════════════════════════

def obtener_admin(auth: tuple = Depends(usuario_actual)) -> tuple[str, dict]:
    """
    Dependencia que:
    1. Primero ejecuta usuario_actual() (reutiliza)
    2. Luego verifica que sea admin
    3. Si no: lanza 403 Forbidden
    """
    nombre_usuario, datos = auth
    requiere_admin(datos)  # ← auth.py
    # Si rol != "admin": lanza HTTPException(403, "...")
    
    return nombre_usuario, datos


# ═══════════════════════════════════════════════════════════════
# USO: Solo en endpoints admin
# ═══════════════════════════════════════════════════════════════

@app.delete("/admin/users/{nombre_usuario}", tags=["admin"])
def admin_eliminar_usuario(nombre_usuario: str, 
                           auth: tuple = Depends(obtener_admin)):
    #                               ↑ inyecta obtener_admin()
    # Que a su vez inyecta usuario_actual()
    
    usuario_admin, _ = auth
    # Ya validado que es admin ✓
```

**Flujo de Dependencias:**
```
Endpoint "/files"
    │
    └─ Depends(usuario_actual)
       │
       ├─ Header(autorizacion)      ← Extrae header
       ├─ cargar_usuarios()          ← Lee users.json
       └─ auth.obtener_usuario_del_token()  ← Valida token
          │
          └─ Si OK: devuelve (usuario, datos)
             Si ERROR: lanza HTTPException(401)


Endpoint "/admin/users/{id}"
    │
    └─ Depends(obtener_admin)
       │
       └─ Depends(usuario_actual)   ← Primero autentica
          │
          └─ auth.requiere_admin()  ← Después autoriza
             │
             └─ Si OK: devuelve (usuario, datos)
                Si ERROR: lanza HTTPException(403)
```

---

## 🔐 Integración Auth

### Flujo de Registro

```python
# ═══════════════════════════════════════════════════════════════
# ENDPOINT: POST /register
# ═══════════════════════════════════════════════════════════════

@app.post("/register", tags=["auth"])
def registrar(nombre_usuario: str, contraseña: str):
    """
    Registro de nuevo usuario.
    Integración con auth.py:
    ├─ hashear_contraseña()
    └─ (genera UUID automático en login)
    """
    
    # Paso 1: Cargar usuarios existentes
    usuarios = cargar_usuarios()  # Lee users.json
    
    # Paso 2: Validaciones
    if nombre_usuario in usuarios:
        raise HTTPException(400, "El nombre de usuario ya existe.")
    
    if len(contraseña) < 6:
        raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")
    
    # Paso 3: Hashear contraseña (auth.py)
    password_hash = hashear_contraseña(contraseña)
    #                ↑ auth.py
    # Devuelve: "salt_aleatorio_hex$hash_hex"
    # Ej: "a1b2c3d4e5f6g7h8$9i10j11k12l13m14n15o16p17q18r19s20"
    
    # Paso 4: Determinar rol
    rol = "admin" if not usuarios else "user"
    # └─ Primer usuario es admin, el resto son users
    
    # Paso 5: Crear entrada de usuario
    usuarios[nombre_usuario] = {
        "password_hash": password_hash,
        "role": rol,
        "session_token": None,  # Se genera después en login
        "areas": {"General": []}  # Área por defecto
    }
    
    # Paso 6: Guardar en users.json
    guardar_usuarios(usuarios)
    
    return {"mensaje": f"Usuario '{nombre_usuario}' registrado.", "rol": rol}
```

**Estructura de users.json:**
```json
{
  "juan": {
    "password_hash": "abc123def$xyz789...",
    "role": "admin",
    "session_token": "550e8400-e29b-41d4-a716-446655440000",
    "areas": {
      "Redes": ["Protocolos", "Topologías"],
      "General": []
    }
  },
  "maria": {
    "password_hash": "def456ghi$uvw012...",
    "role": "user",
    "session_token": null,
    "areas": {
      "Seguridad": [],
      "General": []
    }
  }
}
```

### Flujo de Login

```python
# ═══════════════════════════════════════════════════════════════
# ENDPOINT: POST /login
# ═══════════════════════════════════════════════════════════════

@app.post("/login", tags=["auth"])
def iniciar_sesion(nombre_usuario: str, contraseña: str):
    """
    Login de usuario.
    Integración con auth.py:
    ├─ verificar_contraseña()  ← Valida contraseña
    └─ generar_token()         ← Crea UUID
    """
    
    # Paso 1: Cargar usuarios
    usuarios = cargar_usuarios()
    
    # Paso 2: Buscar usuario
    if nombre_usuario not in usuarios:
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    
    # Paso 3: Verificar contraseña (auth.py)
    password_almacenado = usuarios[nombre_usuario]["password_hash"]
    
    if not verificar_contraseña(contraseña, password_almacenado):
    #      ↑ auth.py
    # ├─ Extrae salt del hash almacenado: "salt$hash"
    # ├─ Calcula PBKDF2(contraseña_ingresada, salt)
    # └─ Compara el nuevo hash con el almacenado
        raise HTTPException(401, "Usuario o contraseña incorrectos.")
    
    # Paso 4: Generar token (auth.py)
    token = generar_token()
    #        ↑ auth.py
    # └─ Crea UUID único (Ej: "550e8400-e29b-41d4-a716-446655440000")
    
    # Paso 5: Guardar token en users.json
    usuarios[nombre_usuario]["session_token"] = token
    guardar_usuarios(usuarios)
    
    # Paso 6: Responder con token
    return {
        "mensaje": "Sesión iniciada.",
        "token": token,
        "rol": usuarios[nombre_usuario]["role"]
    }
```

**Flujo de Seguridad de Contraseña:**
```
1. REGISTRO:
   Contraseña ingresada: "MiPassword123"
   └─ hashear_contraseña("MiPassword123")
      ├─ salt = random(16 bytes).hex()        → "a1b2c3d4e5f6g7h8"
      ├─ hash = PBKDF2-SHA256(pwd, salt, 100k iteraciones)
      └─ almacenado: "a1b2c3d4e5f6g7h8$xyz789..."
      
2. LOGIN:
   Contraseña ingresada: "MiPassword123"
   └─ verificar_contraseña("MiPassword123", "a1b2c3d4e5f6g7h8$xyz789...")
      ├─ salt = "a1b2c3d4e5f6g7h8"  (extrae del almacenado)
      ├─ nuevo_hash = PBKDF2-SHA256("MiPassword123", salt, 100k)
      └─ ¿nuevo_hash == hash_almacenado? → Sí ✓
      
3. INTENTO FALLIDO:
   Contraseña ingresada: "WrongPassword"
   └─ verificar_contraseña("WrongPassword", "a1b2c3d4e5f6g7h8$xyz789...")
      ├─ salt = "a1b2c3d4e5f6g7h8"
      ├─ nuevo_hash = PBKDF2-SHA256("WrongPassword", salt, 100k)
      └─ ¿nuevo_hash == hash_almacenado? → No ✗
         → HTTPException(401, "Usuario o contraseña incorrectos.")
```

---

## 🚪 Integración Gateway

```python
# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE: LoggingMiddleware (gateway.py)
# ═══════════════════════════════════════════════════════════════

# En main.py:
app.add_middleware(LoggingMiddleware)

# Cómo funciona:
# 1. Cada request HTTP entra al middleware
# 2. Se registra el tiempo de inicio
# 3. Se ejecuta el endpoint
# 4. Se registra el tiempo final
# 5. Se imprime: "[GATEWAY] METHOD RUTA → CÓDIGO (TIEMPOs)"

# Ejemplo de logs:
# [GATEWAY] POST /upload → 200 (2.543s)
# [GATEWAY] GET /files → 200 (0.234s)
# [GATEWAY] DELETE /document → 404 (0.087s)


# ═══════════════════════════════════════════════════════════════
# VALIDACIÓN: validar_carga() (gateway.py)
# ═══════════════════════════════════════════════════════════════

@app.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...),
                        auth: tuple = Depends(usuario_actual)):
    """
    Carga un PDF.
    Integración con gateway.py:
    └─ validar_carga()  ← Valida PDF
    """
    
    # Paso 1: VALIDACIÓN (gateway.py)
    validar_carga(archivo)
    #   ↑ gateway.py
    # Verifica:
    # ├─ ¿Termina en .pdf?
    # ├─ ¿Tamaño < 10 MB? (TAM_MAX_ARCHIVOS_MB = 10)
    # └─ Si falla: HTTPException(400) o HTTPException(413)
    
    # Si validar_carga() lanza excepción, esto se detiene
    # Si pasa, continuamos
    
    # Paso 2: Extraer usuario
    nombre_usuario, datos_usuario = auth
    
    # Paso 3: Resto del procesamiento...
    # (continuará con consensus y adapter)


# ═══════════════════════════════════════════════════════════════
# TABLA DE VALIDACIONES
# ═══════════════════════════════════════════════════════════════

# gateway.py:
# 
# def validar_carga(archivo: UploadFile):
#     if not archivo.filename.lower().endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Solo PDFs")
#     
#     if archivo.size and archivo.size > 10 * 1024 * 1024:  # 10 MB
#         raise HTTPException(status_code=413, detail="Archivo muy grande")

# Códigos HTTP:
# ├─ 400 Bad Request:  No es PDF
# ├─ 413 Payload Too Large: Archivo > 10 MB
# └─ 200 OK: Validación pasó
```

---

## 🤝 Integración Consensus

```python
# ═══════════════════════════════════════════════════════════════
# FLUJO COMPLETO DE CONSENSO EN /upload
# ═══════════════════════════════════════════════════════════════

@app.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...),
                        auth: tuple = Depends(usuario_actual)):
    
    nombre_usuario, datos_usuario = auth
    validar_carga(archivo)
    
    # ─────────────────────────────────────────────────────────
    # Paso 1: Preparar áreas para workers (adapter.py)
    # ─────────────────────────────────────────────────────────
    
    áreas_usuario = datos_usuario["areas"]
    # Ej: {"Redes": ["Protocolos", "Topologías"], "General": []}
    
    áreas_planas = construir_áreas_planas(áreas_usuario)
    #                ↑ adapter.py
    # Devuelve: ["Redes", "Protocolos", "Topologías", "General"]
    # (Sin duplicados)
    
    # ─────────────────────────────────────────────────────────
    # Paso 2: Guardar archivo temporalmente
    # ─────────────────────────────────────────────────────────
    
    ruta_temporal = f"temp_{nombre_usuario}_{archivo.filename}"
    with open(ruta_temporal, "wb") as buf:
        shutil.copyfileobj(archivo.file, buf)
    # └─ Escribe el contenido del PDF en disco
    
    # ─────────────────────────────────────────────────────────
    # Paso 3: CLASIFICACIÓN POR CONSENSO (consensus.py)
    # ─────────────────────────────────────────────────────────
    
    try:
        predicho, votos = clasificar_con_consenso(ruta_temporal, áreas_planas)
        #                  ↑ consensus.py
        
        # consensus.py hace lo siguiente:
        # 
        # 1. ENVÍA A WORKERS (3 peticiones paralelas):
        #    
        #    POST http://localhost:5001/process
        #    ├─ file: (PDF bytes)
        #    └─ user_areas: ["Redes", "Protocolos", ...]
        #    → Respuesta: {"area": "Redes"}
        #    
        #    POST http://localhost:5002/process
        #    ├─ file: (PDF bytes)
        #    └─ user_areas: ["Redes", "Protocolos", ...]
        #    → Respuesta: {"area": "Redes"}
        #    
        #    POST http://localhost:5003/process
        #    ├─ file: (PDF bytes)
        #    └─ user_areas: ["Redes", "Protocolos", ...]
        #    → Respuesta: {"area": "Seguridad"}
        #    
        # 2. RECOPILA VOTOS:
        #    votos = {
        #      "node1": "Redes",
        #      "node2": "Redes",
        #      "node3": "Seguridad"
        #    }
        #    resultados = ["Redes", "Redes", "Seguridad"]
        #    
        # 3. CALCULA MAYORÍA:
        #    max(set(resultados), key=resultados.count)
        #    = max({"Redes", "Seguridad"}, key=count)
        #    = "Redes"  (aparece 2 veces)
        #    
        # 4. DEVUELVE:
        #    ("Redes", {"node1": "Redes", "node2": "Redes", "node3": "Seguridad"})
        
        print(f"[CLASIFICACIÓN] Predicción: {predicho}")
        print(f"[CLASIFICACIÓN] Votos: {votos}")
        
    finally:
        # Limpia archivo temporal
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
    
    # ─────────────────────────────────────────────────────────
    # Paso 4: RESOLVER ÁREA (adapter.py)
    # ─────────────────────────────────────────────────────────
    
    area, subarea = resolver_area(predicho, áreas_usuario)
    #                ↑ adapter.py
    
    # resolver_area() busca en la jerarquía:
    # ├─ ¿predicho es área nivel 1?
    # ├─ ¿predicho es área nivel 2?
    # └─ Si no encuentra: ("General", "")
    
    # Ejemplos:
    # resolver_area("Redes", áreas_usuario)
    #   → ("Redes", "")
    # 
    # resolver_area("Protocolos", áreas_usuario)
    #   → ("Redes", "Protocolos")
    # 
    # resolver_area("NoExiste", áreas_usuario)
    #   → ("General", "")
    
    # ─────────────────────────────────────────────────────────
    # Paso 5: REPLICAR EN 3 NODOS
    # ─────────────────────────────────────────────────────────
    
    nodos_almacenados = []
    for nodo in NODOS:  # ["node1", "node2", "node3"]
        directorio_destino = os.path.join(
            BASE_ALMACENAMIENTO,  # "./storage/"
            nodo,                  # "node1"
            nombre_usuario,        # "juan"
            area,                  # "Redes"
            subarea if subarea else ""  # "Protocolos" o ""
        )
        # ├─ Ruta completa: "./storage/node1/juan/Redes/Protocolos/"
        
        os.makedirs(directorio_destino, exist_ok=True)
        shutil.copy(ruta_temporal, 
                   os.path.join(directorio_destino, archivo.filename))
        nodos_almacenados.append(nodo)
    
    # ─────────────────────────────────────────────────────────
    # Paso 6: GUARDAR METADATOS
    # ─────────────────────────────────────────────────────────
    
    metadatos = cargar_metadatos(nombre_usuario)
    # └─ Lee ./metadata/users/juan.json
    
    metadatos["files"].append({
        "name": archivo.filename,
        "area": area,
        "subarea": subarea,
        "nodes": nodos_almacenados,
        "votos": votos,
        "version": 1
    })
    
    guardar_metadatos(nombre_usuario, metadatos)
    # └─ Escribe ./metadata/users/juan.json
    
    # ─────────────────────────────────────────────────────────
    # Paso 7: FORMATEAR RESPUESTA (adapter.py)
    # ─────────────────────────────────────────────────────────
    
    return adaptar_respuesta_carga(archivo.filename, area, subarea, 
                                   nodos_almacenados, votos)
    #      ↑ adapter.py
    # 
    # adaptar_respuesta_carga() devuelve:
    # {
    #   "mensaje": "Archivo procesado correctamente.",
    #   "archivo": "paper.pdf",
    #   "clasificado_en": "Redes/Protocolos",
    #   "area": "Redes",
    #   "subarea": "Protocolos",
    #   "replicado_en": ["node1", "node2", "node3"],
    #   "consenso": {
    #     "votos_por_nodo": {
    #       "node1": "Redes",
    #       "node2": "Redes",
    #       "node3": "Seguridad"
    #     },
    #     "resultado": "Redes/Protocolos"
    #   }
    # }
```

---

## 🔄 Integración Adapter

```python
# ═══════════════════════════════════════════════════════════════
# FUNCIÓN: construir_áreas_planas()
# ═══════════════════════════════════════════════════════════════

# Usado en: /upload (antes de enviar a workers)

áreas_usuario = {
    "Redes": ["Protocolos", "Topologías"],
    "Seguridad": [],
    "General": []
}

áreas_planas = construir_áreas_planas(áreas_usuario)
# └─ ["Redes", "Seguridad", "General", "Protocolos", "Topologías"]

# Devuelve:
# 1. Todas las áreas nivel 1
# 2. Todas las subáreas (nivel 2)
# 3. Sin duplicados (usa set)
# 4. Orden: nivel 1 primero, nivel 2 después


# ═══════════════════════════════════════════════════════════════
# FUNCIÓN: resolver_area()
# ═══════════════════════════════════════════════════════════════

# Usado en: /upload (después de consenso)

# CASO 1: Predicción es área nivel 1
predicho = "Redes"
resolver_area(predicho, áreas_usuario)
# ├─ ¿"Redes" in áreas_usuario? → Sí
# └─ Devuelve: ("Redes", "")

# CASO 2: Predicción es subárea nivel 2
predicho = "Protocolos"
resolver_area(predicho, áreas_usuario)
# ├─ ¿"Protocolos" in áreas_usuario? → No
# ├─ ¿"Protocolos" in áreas_usuario["Redes"]? → Sí
# └─ Devuelve: ("Redes", "Protocolos")

# CASO 3: Predicción no existe
predicho = "NoExiste"
resolver_area(predicho, áreas_usuario)
# ├─ No encontrada en nivel 1
# ├─ No encontrada en nivel 2
# └─ Devuelve: ("General", "")  (fallback)


# ═══════════════════════════════════════════════════════════════
# FUNCIÓN: adaptar_respuesta_carga()
# ═══════════════════════════════════════════════════════════════

# Usado en: /upload (respuesta al cliente)

adaptar_respuesta_carga(
    nombre_archivo="paper.pdf",
    area="Redes",
    subarea="Protocolos",
    nodos=["node1", "node2", "node3"],
    votos={"node1": "Redes", "node2": "Redes", "node3": "Seguridad"}
)

# Devuelve un dict formateado:
{
    "mensaje": "Archivo procesado correctamente.",
    "archivo": "paper.pdf",
    "clasificado_en": "Redes/Protocolos",  # ruta = area/subarea
    "area": "Redes",
    "subarea": "Protocolos",
    "replicado_en": ["node1", "node2", "node3"],
    "consenso": {
        "votos_por_nodo": {...},
        "resultado": "Redes/Protocolos"
    }
}


# ═══════════════════════════════════════════════════════════════
# FUNCIÓN: adaptar_respuesta_archivos()
# ═══════════════════════════════════════════════════════════════

# Usado en: /files (respuesta al cliente)

# Entrada: árbol de 2 niveles construido en main.py
arbol = {
    "Redes": {
        "files": ["paper1.pdf", "paper2.pdf"],
        "Protocolos": {"files": ["paper3.pdf"]},
        "Topologías": {"files": []}
    },
    "General": {
        "files": ["paper4.pdf"]
    }
}

adaptar_respuesta_archivos("juan", arbol)

# Devuelve:
{
    "usuario": "juan",
    "total_archivos": 4,  # Cuenta todos los files
    "clasificacion": arbol  # El árbol tal cual
}
```

---

## 🚨 Manejo de Errores

```python
# ═══════════════════════════════════════════════════════════════
# TABLA DE EXCEPCIONES (HTTPException)
# ═══════════════════════════════════════════════════════════════

# AUTENTICACIÓN (auth.py)
HTTPException(401, "Se requiere Authorization: Bearer <token>")
HTTPException(401, "Token inválido o sesión expirada.")
HTTPException(401, "Usuario o contraseña incorrectos.")

# AUTORIZACIÓN (auth.py)
HTTPException(403, "Se requieren permisos de administrador.")

# VALIDACIÓN (gateway.py)
HTTPException(400, "Solo se aceptan archivos PDF.")
HTTPException(413, "El archivo supera el límite de 10 MB.")

# REGISTRO (main.py)
HTTPException(400, "El nombre de usuario ya existe.")
HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")

# ÁREAS (main.py)
HTTPException(404, f"El área '{area}' no existe.")
HTTPException(400, f"El área '{area}' ya existe.")
HTTPException(400, f"El área '{area}' contiene documentos. Elimínalos primero.")

# CONSENSO (consensus.py)
HTTPException(503, "Ningún worker disponible. Verifica que estén corriendo.")

# DESCARGA (main.py)
HTTPException(404, "Archivo no encontrado en ningún nodo.")


# ═══════════════════════════════════════════════════════════════
# EJEMPLO: Manejo de Error en /upload
# ═══════════════════════════════════════════════════════════════

@app.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...),
                        auth: tuple = Depends(usuario_actual)):
    
    try:
        # POSIBLES ERRORES:
        
        # 1. Auth falla (401)
        #    → usuario_actual() lanza HTTPException(401)
        
        # 2. Archivo inválido (400 / 413)
        #    → validar_carga() lanza HTTPException
        
        # 3. Workers no disponibles (503)
        #    → clasificar_con_consenso() lanza HTTPException
        
        # 4. Errores de filesystem
        #    → os.makedirs(), shutil.copy() lanzan OSError
        
        validar_carga(archivo)
        predicho, votos = clasificar_con_consenso(ruta_temporal, áreas_planas)
        
        # Si todos pasan, continúa
        # Si alguno falla, FastAPI automáticamente:
        # ├─ Captura la excepción
        # ├─ Devuelve respuesta JSON con status_code
        # └─ No se ejecuta el código siguiente
        
    finally:
        # Limpieza siempre se ejecuta
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


# ═══════════════════════════════════════════════════════════════
# FLUJO DE ERROR EN CONSENSO
# ═══════════════════════════════════════════════════════════════

# En consensus.py:
def clasificar_con_consenso(ruta_pdf, áreas_planas):
    votos = {}
    resultados = []
    
    for i, url in enumerate(WORKERS):
        nodo = f"node{i + 1}"
        area = enviar_a_worker(url, ruta_pdf, áreas_planas)
        # └─ Si el worker no responde: area = None
        
        if area is not None:
            votos[nodo] = area
            resultados.append(area)
        else:
            votos[nodo] = "sin respuesta"
    
    if not resultados:
        # Ningún worker respondió
        raise HTTPException(503, "Ningún worker disponible...")
    
    # Si al menos uno respondió, calcula mayoría
    area_final = max(set(resultados), key=resultados.count)
    return area_final, votos
```

---

## 📊 Resumen: Flujo de Datos Completo

```
┌─────────────────────────┐
│ Cliente envía request   │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ FastAPI (main.py)                │
│                                  │
│ 1. LoggingMiddleware (gateway)   │
│    └─ Registra tiempo            │
│                                  │
│ 2. usuario_actual()              │
│    └─ auth.obtener_usuario_del   │
│       _token(token, usuarios)    │
│                                  │
│ 3. gateway.validar_carga()       │
│    └─ ¿PDF válido?               │
│                                  │
│ 4. adapter.construir_áreas_      │
│    planas(áreas_usuario)         │
│    └─ Prepara para workers       │
│                                  │
│ 5. consensus.clasificar_con_     │
│    consenso(pdf, áreas)          │
│    └─ Distribuye a 3 workers     │
│       y calcula mayoría          │
│                                  │
│ 6. adapter.resolver_area()       │
│    └─ Mapea a jerarquía          │
│                                  │
│ 7. Replicación en 3 nodos        │
│    └─ Guarda en storage/         │
│                                  │
│ 8. cargar/guardar_metadatos()    │
│    └─ Actualiza JSON             │
│                                  │
│ 9. adapter.adaptar_respuesta     │
│    └─ Formatea JSON de respuesta │
└────────┬──────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Cliente recibe respuesta│
└─────────────────────────┘
```

---

## 🎯 Checklist de Integración

- ✅ **auth.py**: Hashing, tokens, autorización
- ✅ **gateway.py**: Logging, validación de PDFs
- ✅ **consensus.py**: Orquestación de workers, consenso
- ✅ **adapter.py**: Mapeo de áreas, formateo de respuestas
- 🔲 **database.py**: Supabase (Fase 4, aún no implementado)

Todos los módulos funcionan juntos en armonía en **main.py**.

