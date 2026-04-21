# 📚 Documentación de Integración - Clasificador Distribuido

## Tabla de Contenidos
1. [Arquitectura General](#arquitectura-general)
2. [Módulos y Responsabilidades](#módulos-y-responsabilidades)
3. [Flujos Principales](#flujos-principales)
4. [Relaciones entre Módulos](#relaciones-entre-módulos)
5. [Stack Tecnológico](#stack-tecnológico)

---

## 🏗️ Arquitectura General

El sistema es una **API REST centralizada (Master)** que actúa como orquestador de un sistema distribuido de clasificación de documentos científicos.

```
┌─────────────────────────────────────────────────────────────┐
│                   Cliente / Frontend                         │
│         (Browser, Mobile, Desktop App)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MASTER (main.py)                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🔐 AUTENTICACIÓN (auth.py)                              ││
│  │  • Login/Register/Logout                                 ││
│  │  • Hashing de contraseñas (PBKDF2)                      ││
│  │  • Validación de tokens (UUID)                          ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🚪 GATEWAY (gateway.py)                                  ││
│  │  • Validación de PDFs                                    ││
│  │  • Middleware de logging                                 ││
│  │  • Control de tamaño máximo (10MB)                      ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🤝 CONSENSO (consensus.py)                              ││
│  │  • Orquesta peticiones a workers                        ││
│  │  • Recopila predicciones                                 ││
│  │  • Calcula mayoría de votos                             ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🔄 ADAPTER (adapter.py)                                  ││
│  │  • Mapea predicciones a áreas del usuario               ││
│  │  • Formatea respuestas                                   ││
│  │  • Resuelve jerarquía 2 niveles                         ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 📦 PERSISTENCIA (JSON / Supabase Phase 4)               ││
│  │  • Usuarios en users.json                                ││
│  │  • Metadatos por usuario                                 ││
│  │  • Replicación en 3 nodos                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                     │ HTTP/gRPC (TCP)
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   WORKER1   │ │   WORKER2   │ │   WORKER3   │
│ localhost:  │ │ localhost:  │ │ localhost:  │
│   5001      │ │   5002      │ │   5003      │
│             │ │             │ │             │
│ • ML Model  │ │ • ML Model  │ │ • ML Model  │
│ • Extractor │ │ • Extractor │ │ • Extractor │
│ • Classifier│ │ • Classifier│ │ • Classifier│
└─────────────┘ └─────────────┘ └─────────────┘
     │               │               │
     └───────────────┼───────────────┘
                     ▼
        ┌──────────────────────────┐
        │  ALMACENAMIENTO (3 NODOS)│
        │  ./storage/              │
        │  ├─ node1/usuario/..     │
        │  ├─ node2/usuario/..     │
        │  └─ node3/usuario/..     │
        └──────────────────────────┘
```

---

## 📋 Módulos y Responsabilidades

### 1️⃣ **auth.py** — Autenticación y Autorización

**Responsabilidad:** Manejar credenciales, tokens y roles de usuario.

**Funciones principales:**
- `hashear_contraseña(contraseña)` → Crea hash PBKDF2-SHA256 + salt
- `verificar_contraseña(contraseña, almacenado)` → Valida contraseña
- `generar_token()` → Crea UUID único para sesión
- `obtener_usuario_del_token(token, usuarios)` → Extrae usuario del token
- `requiere_admin(datos_usuario)` → Valida permisos de admin

**¿Cuándo se usa?**
```python
# En main.py, en la dependencia usuario_actual()
def usuario_actual(autorizacion: str = Header(...)) -> tuple[str, dict]:
    token = autorizacion[7:]  # Extrae "Bearer xxxxx"
    usuarios = cargar_usuarios()
    return obtener_usuario_del_token(token, usuarios)  # ← auth.py

# Cada endpoint autenticado usa:
@app.get("/files", tags=["documentos"])
def obtener_archivos(auth: tuple = Depends(usuario_actual)):
    nombre_usuario, datos_usuario = auth
    # Ahora tengo al usuario validado
```

**Algoritmo de seguridad:**
```
Contraseña → PBKDF2(SHA256, iteraciones=100k, salt aleatorio)
           → "salt_aleatorio$hash_hexadecimal"
           → Guardado en users.json
```

---

### 2️⃣ **gateway.py** — Validación y Logging

**Responsabilidad:** Primera línea de validación + monitoreo de peticiones.

**Funciones principales:**
- `LoggingMiddleware` → Middleware que registra tiempo y código HTTP de cada request
- `validar_carga(archivo)` → Verifica que sea PDF y < 10MB

**¿Cuándo se usa?**
```python
# En main.py
app.add_middleware(LoggingMiddleware)  # ← Middleware global

@app.post("/upload", tags=["documentos"])
async def cargar_archivo(archivo: UploadFile = File(...), ...):
    validar_carga(archivo)  # ← gateway.py valida
    # Si falla: 400 (no PDF) o 413 (muy grande)
```

**Registro de logs:**
```
[GATEWAY] POST /upload → 200 (0.542s)
[GATEWAY] GET /files → 200 (0.123s)
[GATEWAY] DELETE /document → 404 (0.045s)
```

---

### 3️⃣ **consensus.py** — Orquestación de Workers

**Responsabilidad:** Contactar a 3 workers en paralelo, recopilar predicciones y elegir por mayoría.

**Funciones principales:**
- `enviar_a_worker(url, ruta_pdf, áreas_planas)` → POST al worker y obtiene predicción
- `clasificar_con_consenso(ruta_pdf, áreas_planas)` → Orquesta todo y devuelve (área_ganadora, votos)

**¿Cuándo se usa?**
```python
# En main.py, en /upload
@app.post("/upload")
async def cargar_archivo(...):
    # ...
    predicho, votos = clasificar_con_consenso(ruta_temporal, áreas_planas)
    #                   ↑ consensus.py
    # Devuelve: ("Redes", {"node1": "Redes", "node2": "Redes", "node3": "Seguridad"})
```

**Flujo de consenso:**
```
Master → node1:5001/process (PDF bytes + áreas planas)
         ↓ espera respuesta
         {"area": "Redes"}
         
Master → node2:5002/process (PDF bytes + áreas planas)
         ↓ espera respuesta
         {"area": "Redes"}
         
Master → node3:5003/process (PDF bytes + áreas planas)
         ↓ espera respuesta
         {"area": "Seguridad"}

Resulta: max(["Redes", "Redes", "Seguridad"]) = "Redes"
Votos: {"node1": "Redes", "node2": "Redes", "node3": "Seguridad"}
```

---

### 4️⃣ **adapter.py** — Transformación de Datos

**Responsabilidad:** Mapear predicciones a la jerarquía del usuario + formatear respuestas.

**Funciones principales:**
- `resolver_area(predicho, áreas_usuario)` → Encuentra (area, subarea) del usuario
- `construir_áreas_planas(áreas_usuario)` → Crea lista para workers
- `adaptar_respuesta_carga(...)` → Formatea JSON de respuesta
- `adaptar_respuesta_archivos(...)` → Formatea árbol de archivos

**¿Cuándo se usa?**
```python
# En main.py, en /upload
áreas_planas = construir_áreas_planas(áreas_usuario)
#              ↑ adapter.py

predicho, votos = clasificar_con_consenso(ruta_temporal, áreas_planas)
area, subarea = resolver_area(predicho, áreas_usuario)
#               ↑ adapter.py

return adaptar_respuesta_carga(archivo.filename, area, subarea, nodos, votos)
       ↑ adapter.py
```

**Ejemplo de resolución:**
```python
áreas_usuario = {
    "Redes": ["Protocolos", "Topologías"],
    "Seguridad": [],
    "General": []
}

predicho = "Protocolos"

resolver_area("Protocolos", áreas_usuario)
# → ("Redes", "Protocolos")  ✓ encontrado como subárea
```

---

### 5️⃣ **database.py** — Persistencia (Fase 4)

**Estado:** 🔲 **PENDIENTE** — Actualmente usa JSON, será Supabase.

**Responsabilidad:** Abstraer acceso a BD (usuarios, documentos, metadatos).

**Funciones por implementar:**
- `obtener_usuario_por_nombre(username)` → Consulta tabla `usuarios`
- `insertar_o_actualizar_usuario(datos)` → Upsert en `usuarios`
- `obtener_documentos_por_usuario(id_usuario)` → SELECT de `documentos`
- `insertar_documento(datos_doc)` → INSERT en `documentos`

**Tablas planeadas:**
```sql
-- Usuarios
CREATE TABLE usuarios (
    id UUID PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'user',
    session_token TEXT,
    created_at TIMESTAMPTZ
);

-- Temáticas (2 niveles: parent_id NULL = nivel 1)
CREATE TABLE tematicas (
    id UUID PRIMARY KEY,
    nombre TEXT,
    nivel INT CHECK (nivel IN (1, 2)),
    parent_id UUID REFERENCES tematicas(id),
    user_id UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ
);

-- Documentos
CREATE TABLE documentos (
    id UUID PRIMARY KEY,
    nombre TEXT,
    tematica_id UUID REFERENCES tematicas(id),
    user_id UUID REFERENCES usuarios(id),
    nodos JSONB,
    votos JSONB,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ
);
```

---

## 🔄 Flujos Principales

### 📤 Flujo 1: Registro e Inicio de Sesión

```
Cliente
   │
   ├─ POST /register (nombre_usuario, contraseña)
   │   └─→ main.py: registrar()
   │       ├─ auth.hashear_contraseña(contraseña)
   │       │  └─→ genera salt + PBKDF2-SHA256 + almacena
   │       ├─ Primer usuario → rol="admin"
   │       ├─ Guarda en users.json
   │       └─ Responde: {"mensaje": "...", "rol": "admin"}
   │
   ├─ POST /login (nombre_usuario, contraseña)
   │   └─→ main.py: iniciar_sesion()
   │       ├─ Carga users.json
   │       ├─ auth.verificar_contraseña(contraseña)
   │       │  └─→ calcula hash nuevo y compara
   │       ├─ auth.generar_token()
   │       │  └─→ crea UUID
   │       ├─ Guarda token en users.json[usuario]["session_token"]
   │       └─ Responde: {"token": "uuid-xxx-xxx", "rol": "user"}
   │
   └─ Clientes futuros usan:
      Authorization: Bearer uuid-xxx-xxx
      └─→ usuario_actual(autorizacion)
          └─→ auth.obtener_usuario_del_token(token, usuarios)
```

---

### 📁 Flujo 2: Carga y Clasificación de PDF

```
Cliente
   │
   └─ POST /upload (archivo.pdf)
      │
      └─→ main.py: cargar_archivo(archivo, auth)
          │
          ├─ [VALIDACIÓN] gateway.validar_carga(archivo)
          │  ├─ ¿Es .pdf?  ✓
          │  ├─ ¿< 10MB?   ✓
          │  └─ Si falla: 400 o 413
          │
          ├─ [PREPARACIÓN] Extrae usuario del token
          │  └─→ auth.obtener_usuario_del_token(token, usuarios)
          │
          ├─ [MAPEO] adapter.construir_áreas_planas(áreas_usuario)
          │  │ Entrada:  {"Redes": ["Protocolos", "Topologías"], "General": []}
          │  └─ Salida:  ["Redes", "Protocolos", "Topologías", "General"]
          │     (Para que workers sepan qué áreas clasificar)
          │
          ├─ [CLASIFICACIÓN] consensus.clasificar_con_consenso(pdf, áreas_planas)
          │  │
          │  ├─ Node1 (localhost:5001) 
          │  │  POST /process (PDF + áreas_planas)
          │  │  ← {"area": "Redes"}
          │  │
          │  ├─ Node2 (localhost:5002)
          │  │  POST /process (PDF + áreas_planas)
          │  │  ← {"area": "Redes"}
          │  │
          │  ├─ Node3 (localhost:5003)
          │  │  POST /process (PDF + áreas_planas)
          │  │  ← {"area": "Seguridad"}
          │  │
          │  └─ Consenso: max_votos("Redes") gana
          │     Devuelve: ("Redes", {"node1": "Redes", ...})
          │
          ├─ [RESOLUCIÓN] adapter.resolver_area(predicho, áreas_usuario)
          │  │ Entrada:  ("Redes", áreas_usuario)
          │  │ ├─ ¿"Redes" es área?        → Sí
          │  │ ├─ ¿Hay subareas?           → ["Protocolos", "Topologías"]
          │  │ └─ Decisión: area="Redes", subarea=""
          │  └─ Salida: ("Redes", "")
          │
          ├─ [REPLICACIÓN] Guarda en storage/ (3 nodos)
          │  ├─ ./storage/node1/usuario/Redes/archivo.pdf
          │  ├─ ./storage/node2/usuario/Redes/archivo.pdf
          │  └─ ./storage/node3/usuario/Redes/archivo.pdf
          │
          ├─ [PERSISTENCIA] cargar_metadatos() + guardar_metadatos()
          │  │ Archivo: ./metadata/users/usuario.json
          │  └─ {"files": [{"name": "...", "area": "Redes", "nodes": [...], ...}]}
          │
          └─ [RESPUESTA] adapter.adaptar_respuesta_carga(...)
             {
               "mensaje": "Archivo procesado correctamente.",
               "archivo": "paper.pdf",
               "clasificado_en": "Redes",
               "area": "Redes",
               "subarea": null,
               "replicado_en": ["node1", "node2", "node3"],
               "consenso": {
                 "votos_por_nodo": {"node1": "Redes", "node2": "Redes", "node3": "Seguridad"},
                 "resultado": "Redes"
               }
             }
```

---

### 📂 Flujo 3: Obtener Árbol de Archivos

```
Cliente
   │
   └─ GET /files (Authorization: Bearer token)
      │
      └─→ main.py: obtener_archivos(auth)
          │
          ├─ Extrae usuario: auth.obtener_usuario_del_token(token, usuarios)
          │
          ├─ Carga áreas del usuario desde users.json
          │  └─ {"Redes": ["Protocolos", "Topologías"], "General": []}
          │
          ├─ Carga metadatos: cargar_metadatos(usuario)
          │  └─ {"files": [{"name": "p1.pdf", "area": "Redes", "subarea": ""}, ...]}
          │
          ├─ Construye árbol vacío con todas las áreas:
          │  {
          │    "Redes": {
          │      "files": [],
          │      "Protocolos": {"files": []},
          │      "Topologías": {"files": []}
          │    },
          │    "General": {"files": []}
          │  }
          │
          ├─ Llena el árbol con archivos del usuario
          │  {
          │    "Redes": {
          │      "files": ["p1.pdf", "p2.pdf"],
          │      "Protocolos": {"files": ["p3.pdf"]},
          │      "Topologías": {"files": []}
          │    },
          │    "General": {"files": ["p4.pdf"]}
          │  }
          │
          └─ [RESPUESTA] adapter.adaptar_respuesta_archivos(usuario, árbol)
             {
               "usuario": "juan",
               "total_archivos": 4,
               "clasificacion": {
                 "Redes": {
                   "files": ["p1.pdf", "p2.pdf"],
                   "Protocolos": {"files": ["p3.pdf"]},
                   "Topologías": {"files": []}
                 },
                 "General": {"files": ["p4.pdf"]}
               }
             }
```

---

### ❌ Flujo 4: Eliminar Documento

```
Cliente
   │
   └─ DELETE /document?nombre_archivo=paper.pdf&area=Redes&subarea=&auth=Bearer token
      │
      └─→ main.py: eliminar_documento(nombre_archivo, area, subarea, auth)
          │
          ├─ Valida usuario: auth.obtener_usuario_del_token(token, usuarios)
          │
          ├─ Busca en los 3 nodos:
          │  ├─ ./storage/node1/usuario/Redes/paper.pdf  ← existe, DELETE
          │  ├─ ./storage/node2/usuario/Redes/paper.pdf  ← existe, DELETE
          │  └─ ./storage/node3/usuario/Redes/paper.pdf  ← existe, DELETE
          │
          ├─ Actualiza metadatos: cargar_metadatos() + guardar_metadatos()
          │  └─ Remueve entrada de "files"
          │
          └─ [RESPUESTA]
             {
               "mensaje": "Archivo 'paper.pdf' eliminado de ['node1', 'node2', 'node3']."
             }
```

---

## 🔗 Relaciones entre Módulos

### Tabla de Dependencias

| Módulo en main.py | Depende de | Cómo se usa |
|---|---|---|
| `registrar()` | `auth.hashear_contraseña()` | Hashea contraseña antes de guardar |
| `iniciar_sesion()` | `auth.verificar_contraseña()`, `auth.generar_token()` | Valida credencial y crea token |
| `usuario_actual()` | `auth.obtener_usuario_del_token()` | Valida token en cada request |
| `obtener_admin()` | `auth.requiere_admin()` | Valida permisos de admin |
| `cargar_archivo()` | `gateway.validar_carga()` | Valida que sea PDF |
| `cargar_archivo()` | `consensus.clasificar_con_consenso()` | Obtiene predicción de workers |
| `cargar_archivo()` | `adapter.construir_áreas_planas()` | Prepara áreas para workers |
| `cargar_archivo()` | `adapter.resolver_area()` | Mapea predicción a jerarquía |
| `cargar_archivo()` | `adapter.adaptar_respuesta_carga()` | Formatea respuesta JSON |
| `obtener_archivos()` | `adapter.adaptar_respuesta_archivos()` | Formatea árbol JSON |

### Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│ Cliente envía PDF                                            │
└────────────────────┬────────────────────────────────────────┘
                     ▼
        ┌────────────────────────┐
        │ gateway.validar_carga()│  ← Valida formato
        └────────┬───────────────┘
                 ▼
    ┌──────────────────────────────┐
    │ adapter.construir_áreas      │  ← Construye lista de áreas
    │     _planas()                │
    └────────┬─────────────────────┘
             ▼
    ┌────────────────────────────────┐
    │ consensus.clasificar_con_      │  ← Distribuye a workers
    │ consenso()                     │     y calcula mayoría
    └────────┬─────────────────────┘
             ▼
    ┌────────────────────────────┐
    │ adapter.resolver_area()    │  ← Mapea a jerarquía
    └────────┬─────────────────┘
             ▼
    ┌────────────────────────────┐
    │ Replicar en 3 nodos        │  ← Almacena en storage/
    └────────┬─────────────────┘
             ▼
    ┌─────────────────────────────┐
    │ cargar_metadatos() +        │  ← Guarda en JSON
    │ guardar_metadatos()         │
    └────────┬────────────────────┘
             ▼
    ┌─────────────────────────────┐
    │ adapter.adaptar_respuesta   │  ← Formatea JSON
    │     _carga()                │
    └────────┬────────────────────┘
             ▼
    ┌─────────────────────────────┐
    │ Cliente recibe respuesta    │
    └─────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend Principal
- **FastAPI** — Framework REST moderno y rápido
- **Python 3.9+** — Lenguaje base
- **Starlette** — ASGI framework (base de FastAPI)

### Autenticación
- **hashlib.pbkdf2_hmac** — Hashing de contraseñas (stdlib)
- **uuid** — Generación de tokens (stdlib)

### Clasificación
- **requests** — HTTP client para contactar workers
- **json** — Serialización de datos

### Persistencia (Actual)
- **JSON** — users.json, metadata/users/*.json
- **Sistema de archivos** — storage/node{1,2,3}/

### Persistencia (Fase 4)
- **Supabase** — BD PostgreSQL en la nube
- **supabase-py** — Cliente Python

### Testing (No implementado)
- **pytest** — Sería el framework de tests
- **httpx** — Cliente HTTP para tests async

---

## 📝 Resumen: ¿Qué Hace Cada Parte?

| Componente | ¿Qué hace? | ¿Cuándo se usa? |
|---|---|---|
| **auth.py** | Hashea/verifica contraseñas, genera/valida tokens | Cada login/request autenticado |
| **gateway.py** | Valida PDFs, registra logs HTTP | Middleware global + antes de procesar PDF |
| **consensus.py** | Contacta 3 workers, calcula mayoría | Al subir un PDF |
| **adapter.py** | Mapea predicciones a áreas, formatea JSON | Mapeo de resultados + respuestas |
| **database.py** | Abstracción a BD (Fase 4) | Cuando Supabase esté integrado |
| **main.py** | Orquesta todo, define endpoints | Siempre — es el corazón del sistema |

---

## 🚀 Ciclo de Vida de un Request Típico

```
1. Cliente → main.py
   ├─ Extrae token del header
   ├─ auth.obtener_usuario_del_token() ← valida usuario
   │
2. main.py → gateway.py
   ├─ gateway.validar_carga() ← valida PDF
   │
3. main.py → adapter.py
   ├─ adapter.construir_áreas_planas() ← prepara datos para workers
   │
4. main.py → consensus.py
   ├─ consensus.clasificar_con_consenso() ← distribuye trabajo
   │  ├─ Contacta node1:5001/process
   │  ├─ Contacta node2:5002/process
   │  ├─ Contacta node3:5003/process
   │  └─ Calcula mayoría de votos
   │
5. main.py → adapter.py
   ├─ adapter.resolver_area() ← mapea predicción a área
   │
6. main.py → Sistema de archivos
   ├─ Replica en storage/node1/, storage/node2/, storage/node3/
   │
7. main.py → JSON files
   ├─ cargar_metadatos() + guardar_metadatos() ← persiste metadatos
   │
8. main.py → adapter.py
   ├─ adapter.adaptar_respuesta_carga() ← formatea JSON
   │
9. main.py → Cliente
   └─ Envía respuesta con resultado
```

---

## 🔐 Capas de Seguridad

```
┌─ Nivel 1: MIDDLEWARE
│  └─ LoggingMiddleware (gateway.py)
│     Registra todas las peticiones
│
├─ Nivel 2: VALIDACIÓN DE ENTRADA
│  └─ gateway.validar_carga()
│     Verifica PDF + tamaño
│
├─ Nivel 3: AUTENTICACIÓN
│  └─ usuario_actual() → auth.obtener_usuario_del_token()
│     Valida token de sesión
│
├─ Nivel 4: AUTORIZACIÓN
│  └─ obtener_admin() → auth.requiere_admin()
│     Verifica rol de admin
│
└─ Nivel 5: ALMACENAMIENTO
   └─ PBKDF2-SHA256 con salt aleatorio
      Hashing seguro de contraseñas
```

---

## 📊 Jerarquía de Datos: 2 Niveles

```
Usuario:
  ├─ Nivel 1 (Temáticas):
  │  ├─ "Redes"
  │  │  ├─ Nivel 2 (Subtemáticas):
  │  │  │  ├─ "Protocolos"
  │  │  │  └─ "Topologías"
  │  │  └─ files: [documentos en Redes sin subárea]
  │  │
  │  ├─ "Seguridad"
  │  │  └─ files: []
  │  │
  │  └─ "General"  (siempre existe)
  │     └─ files: [documentos sin clasificar]
  │
  └─ Archivos esparcidos por la jerarquía
```

---

## 🎯 Conclusión

El **main.py** actúa como el **director de orquesta** que:

1. **Autentica** usuarios (auth.py)
2. **Valida** solicitudes (gateway.py)
3. **Distribuye** trabajo a workers (consensus.py)
4. **Mapea** resultados a la jerarquía del usuario (adapter.py)
5. **Replica** en 3 nodos (sistema de archivos)
6. **Persiste** metadatos (JSON)
7. **Responde** al cliente (adapter.py)

Todos los módulos son especializados y reutilizables, facilitando testing y mantenimiento.

