# 📊 Diagramas y Resumen Visual

## 1️⃣ Diagrama de Arquitectura General

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                         CLIENTE (Frontend/Mobile)                              ║
╚═════════════════════════════════════╦══════════════════════════════════════════╝
                                      │ HTTP REST
                                      ▼
╔════════════════════════════════════════════════════════════════════════════════╗
║                          MASTER API (main.py)                                   ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 🔐 AUTENTICACIÓN (auth.py)                                               │  ║
║  │                                                                          │  ║
║  │  POST /register  →  hashear_contraseña()  →  users.json                │  ║
║  │  POST /login     →  verificar_contraseña()  →  generar_token()         │  ║
║  │  POST /logout    →  invalidar_token()                                  │  ║
║  │                                                                          │  ║
║  │  Cada request usa: usuario_actual() = Depends() → valida token         │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 🚪 GATEWAY (gateway.py)                                                  │  ║
║  │                                                                          │  ║
║  │  LoggingMiddleware  →  Registra: [GATEWAY] METHOD RUTA → CODE (Ts)     │  ║
║  │  validar_carga()    →  ¿Es PDF? ¿< 10MB?                              │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 📂 GESTIÓN DE ÁREAS (main.py)                                            │  ║
║  │                                                                          │  ║
║  │  GET    /categories   →  Devuelve jerarquía del usuario               │  ║
║  │  POST   /areas        →  Crear temática nivel 1                        │  ║
║  │  POST   /areas/{a}/sub →  Crear subtemática nivel 2                    │  ║
║  │  DELETE /areas/{a}    →  Eliminar si está vacía                        │  ║
║  │  DELETE /areas/{a}/sub/{s} → Eliminar subtemática si está vacía        │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 📄 GESTIÓN DE DOCUMENTOS (main.py)                                       │  ║
║  │                                                                          │  ║
║  │  POST   /upload        →  Carga PDF, clasifica, replica, persiste      │  ║
║  │  GET    /files         →  Devuelve árbol de archivos                   │  ║
║  │  GET    /download      →  Descarga archivo (intenta 3 nodos)           │  ║
║  │  DELETE /document      →  Elimina de 3 nodos y metadatos               │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 👨‍💼 ADMINISTRACIÓN (main.py)                                              │  ║
║  │                                                                          │  ║
║  │  GET    /admin/users           →  Lista usuarios                        │  ║
║  │  POST   /admin/users           →  Crear usuario (solo admin)           │  ║
║  │  DELETE /admin/users/{u}       →  Eliminar usuario                     │  ║
║  │  PUT    /admin/users/{u}       →  Modificar usuario                    │  ║
║  │  DELETE /admin/areas/{u}/{a}   →  Eliminar área (fuerza)              │  ║
║  │  DELETE /admin/areas/{u}/{a}/{s} → Eliminar subárea (fuerza)          │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 🤝 CONSENSO (consensus.py)                                              │  ║
║  │                                                                          │  ║
║  │  Contacta 3 workers en paralelo:                                        │  ║
║  │    → POST http://localhost:5001/process                                 │  ║
║  │    → POST http://localhost:5002/process                                 │  ║
║  │    → POST http://localhost:5003/process                                 │  ║
║  │                                                                          │  ║
║  │  Recopila votos → Calcula max(votos) → Devuelve (área_ganadora, votos) │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 🔄 ADAPTER (adapter.py)                                                 │  ║
║  │                                                                          │  ║
║  │  construir_áreas_planas()  →  ["Redes", "Protocolos", "General", ...] │  ║
║  │  resolver_area()           →  Mapea predicción a jerarquía             │  ║
║  │  adaptar_respuesta_*       →  Formatea JSON para cliente               │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
║  ┌──────────────────────────────────────────────────────────────────────────┐  ║
║  │ 💾 PERSISTENCIA                                                          │  ║
║  │                                                                          │  ║
║  │  ./metadata/users.json          →  Usuarios + contraseñas              │  ║
║  │  ./metadata/users/{usuario}.json →  Metadatos de archivos              │  ║
║  │  ./storage/node{1,2,3}/...      →  Replicación en 3 nodos            │  ║
║  │                                                                          │  ║
║  │  FASE 4: Supabase (PostgreSQL)                                         │  ║
║  └──────────────────────────────────────────────────────────────────────────┘  ║
╚════════════════════════════════════════════════════════════════════════════════╝
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ WORKERS (worker/main.py) - 3 Instancias                                          │
│                                                                                  │
│  Worker 1            Worker 2            Worker 3                               │
│  :5001               :5002               :5003                                  │
│  ├─ Extractor       ├─ Extractor       ├─ Extractor                             │
│  ├─ Classifier      ├─ Classifier      ├─ Classifier                            │
│  └─ Sync            └─ Sync            └─ Sync                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2️⃣ Flujo de /upload (Carga de PDF)

```
┌──────────────────────────────────┐
│  POST /upload (PDF + token)      │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  ✓ Validar header Authorization  │  → auth.obtener_usuario_del_token()
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  ✓ Validar PDF (¿existe? ¿<10MB?)│  → gateway.validar_carga()
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  ✓ Construir áreas_planas            │  → adapter.construir_áreas_planas()
│                                      │     ["Redes", "Protocolos", ...]
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  ✓ Guardar PDF temporal              │
│    Ej: temp_juan_paper.pdf           │
└──────────┬──────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────┐
│  🤝 CONSENSO: Contactar 3 workers                              │
│                                                                │
│  ┌─ node1 ──────────────────────────────────┐                 │
│  │ POST http://localhost:5001/process       │                 │
│  │  file: paper.pdf                         │                 │
│  │  user_areas: ["Redes", "Protocolos", ...] │                 │
│  │  ↓ Respuesta: {"area": "Redes"}           │                 │
│  └──────────────────────────────────────────┘                 │
│                                                                │
│  ┌─ node2 ──────────────────────────────────┐                 │
│  │ POST http://localhost:5002/process       │                 │
│  │  file: paper.pdf                         │                 │
│  │  user_areas: ["Redes", "Protocolos", ...] │                 │
│  │  ↓ Respuesta: {"area": "Redes"}           │                 │
│  └──────────────────────────────────────────┘                 │
│                                                                │
│  ┌─ node3 ──────────────────────────────────┐                 │
│  │ POST http://localhost:5003/process       │                 │
│  │  file: paper.pdf                         │                 │
│  │  user_areas: ["Redes", "Protocolos", ...] │                 │
│  │  ↓ Respuesta: {"area": "Seguridad"}       │                 │
│  └──────────────────────────────────────────┘                 │
│                                                                │
│  Votos: {"node1": "Redes", "node2": "Redes", "node3": ...}   │
│  Mayoría: "Redes" (2 de 3) ✓                                  │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  ✓ Resolver área en jerarquía        │  → adapter.resolver_area()
│    predicho="Redes"                  │     Busca en áreas_usuario
│    ↓ Resultado: ("Redes", "")        │
└──────────┬──────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────────────────┐
│  ✓ Replicar en 3 nodos                                         │
│                                                                │
│  ./storage/node1/juan/Redes/paper.pdf  ✓                      │
│  ./storage/node2/juan/Redes/paper.pdf  ✓                      │
│  ./storage/node3/juan/Redes/paper.pdf  ✓                      │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  ✓ Actualizar metadatos              │
│  ./metadata/users/juan.json           │
│  Agrega a "files": [{name, area, ...}]│
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  ✓ Formatear respuesta JSON          │  → adapter.adaptar_respuesta_carga()
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  {                                    │
│    "mensaje": "Procesado...",         │
│    "archivo": "paper.pdf",            │
│    "area": "Redes",                   │
│    "subarea": null,                   │
│    "clasificado_en": "Redes",         │
│    "replicado_en": [                  │
│      "node1", "node2", "node3"        │
│    ],                                 │
│    "consenso": {                      │
│      "votos_por_nodo": {...},         │
│      "resultado": "Redes"             │
│    }                                  │
│  }                                    │
└──────────────────────────────────────┘
```

---

## 3️⃣ Flujo de Autenticación

```
┌─────────────────────────────────┐
│ REGISTRO (POST /register)       │
└────────┬────────────────────────┘
         │
         ├─ ¿Usuario existe? → 400 Bad Request
         │
         ├─ ¿Contraseña >= 6 chars? → 400 Bad Request
         │
         ▼
    ┌────────────────────────────┐
    │ hashear_contraseña(pwd)    │  ← auth.py
    │ ↓ genera salt aleatorio    │
    │ ↓ PBKDF2-SHA256(pwd, salt) │
    │ ↓ devuelve "salt$hash"     │
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ Guardar en users.json      │
    │ {                          │
    │   "juan": {                │
    │     "password_hash":       │
    │       "abc$xyz...",        │
    │     "role": "admin",  ← primer usuario
    │     "session_token": null, │
    │     "areas": {...}         │
    │   }                        │
    │ }                          │
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ 200 OK                     │
    │ {                          │
    │   "mensaje": "Registrado", │
    │   "rol": "admin"           │
    │ }                          │
    └────────────────────────────┘


┌─────────────────────────────┐
│ LOGIN (POST /login)         │
└────────┬────────────────────┘
         │
         ├─ ¿Usuario existe? → 401 Unauthorized
         │
         ▼
    ┌────────────────────────────┐
    │ verificar_contraseña()     │  ← auth.py
    │ ├─ extrae salt del hash    │
    │ │  almacenado              │
    │ ├─ calcula nuevo PBKDF2    │
    │ └─ compara con almacenado  │
    └────────┬───────────────────┘
             │
         ❌ Falla → 401 Unauthorized
             │
         ✓ Pasa
             │
             ▼
    ┌────────────────────────────┐
    │ generar_token()            │  ← auth.py
    │ ├─ crea UUID único         │
    │ └─ ej: 550e8400-e29b-...   │
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ Guardar en users.json      │
    │ usuarios[juan]             │
    │  ["session_token"] = token │
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ 200 OK                     │
    │ {                          │
    │   "token": "550e8400...",  │
    │   "rol": "admin"           │
    │ }                          │
    └────────────────────────────┘


┌─────────────────────────────┐
│ REQUESTS CON TOKEN          │
│ Authorization: Bearer token │
└────────┬────────────────────┘
         │
         ▼
    ┌────────────────────────────────┐
    │ usuario_actual(header)         │
    │ └─ Depends() inyectada         │
    └────────┬───────────────────────┘
             │
             ├─ ¿Empieza con "Bearer "? → 401
             │
             ├─ Extrae token
             │
             ▼
    ┌────────────────────────────────┐
    │ obtener_usuario_del_token()    │  ← auth.py
    │ ├─ carga users.json            │
    │ ├─ busca quién tiene el token  │
    │ └─ devuelve (usuario, datos)   │
    └────────┬───────────────────────┘
             │
         ❌ No encontrado → 401
             │
         ✓ Encontrado
             │
             ▼
    ┌────────────────────────────┐
    │ Endpoint continúa          │
    │ con usuario validado       │
    └────────────────────────────┘


┌──────────────────────────────┐
│ LOGOUT (POST /logout)        │
└────────┬─────────────────────┘
         │
         ├─ Valida usuario (usuario_actual)
         │
         ▼
    ┌────────────────────────────┐
    │ Nullificar session_token   │
    │ usuarios[juan]             │
    │  ["session_token"] = null  │
    └────────┬───────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ 200 OK                     │
    │ {"mensaje": "Cerrada"}     │
    └────────────────────────────┘
```

---

## 4️⃣ Jerarquía de Áreas (2 Niveles)

```
Usuario Juan
│
├─ TEMÁTICAS (Nivel 1)
│  │
│  ├─ "Redes"  (area)
│  │  │
│  │  ├─ SUBTEMÁTICAS (Nivel 2)
│  │  │  │
│  │  │  ├─ "Protocolos" (subarea)
│  │  │  │  └─ Documentos:
│  │  │  │     ├─ paper1.pdf
│  │  │  │     └─ paper2.pdf
│  │  │  │
│  │  │  └─ "Topologías" (subarea)
│  │  │     └─ Documentos:
│  │  │        └─ paper3.pdf
│  │  │
│  │  └─ Documentos (sin subárea):
│  │     └─ (ninguno)
│  │
│  ├─ "Seguridad" (area)
│  │  │
│  │  ├─ SUBTEMÁTICAS: (ninguna)
│  │  │
│  │  └─ Documentos:
│  │     └─ (ninguno)
│  │
│  └─ "General" (area reservada)
│     │
│     ├─ SUBTEMÁTICAS: (siempre vacía)
│     │
│     └─ Documentos:
│        ├─ paper4.pdf (no clasificado)
│        └─ paper5.pdf (fallback)

Estructura en users.json:
{
  "juan": {
    "password_hash": "...",
    "role": "user",
    "session_token": "uuid",
    "areas": {
      "Redes": ["Protocolos", "Topologías"],
      "Seguridad": [],
      "General": []
    }
  }
}

Estructura en metadata/users/juan.json:
{
  "files": [
    {
      "name": "paper1.pdf",
      "area": "Redes",
      "subarea": "Protocolos",
      "nodes": ["node1", "node2", "node3"],
      "votos": {"node1": "Redes", ...},
      "version": 1
    },
    ...
  ]
}

Respuesta GET /files:
{
  "usuario": "juan",
  "total_archivos": 5,
  "clasificacion": {
    "Redes": {
      "files": [],  ← sin subárea
      "Protocolos": {
        "files": ["paper1.pdf", "paper2.pdf"]
      },
      "Topologías": {
        "files": ["paper3.pdf"]
      }
    },
    "Seguridad": {
      "files": []
    },
    "General": {
      "files": ["paper4.pdf", "paper5.pdf"]
    }
  }
}
```

---

## 5️⃣ Almacenamiento en Disco

```
./storage/
├─ node1/
│  └─ juan/
│     ├─ Redes/
│     │  ├─ Protocolos/
│     │  │  ├─ paper1.pdf
│     │  │  └─ paper2.pdf
│     │  ├─ Topologías/
│     │  │  └─ paper3.pdf
│     │  └─ (archivo en Redes sin subárea)
│     ├─ Seguridad/
│     │  └─ (vacía)
│     └─ General/
│        ├─ paper4.pdf
│        └─ paper5.pdf
│
├─ node2/
│  └─ juan/
│     ├─ Redes/
│     │  ├─ Protocolos/
│     │  │  ├─ paper1.pdf  ← RÉPLICA
│     │  │  └─ paper2.pdf  ← RÉPLICA
│     │  └─ ...
│
└─ node3/
   └─ juan/
      ├─ Redes/
      │  ├─ Protocolos/
      │  │  ├─ paper1.pdf  ← RÉPLICA
      │  │  └─ paper2.pdf  ← RÉPLICA
      │  └─ ...

./metadata/
├─ users.json  ← Usuarios + credenciales
│
└─ users/
   ├─ juan.json  ← Metadatos de archivos de juan
   ├─ maria.json ← Metadatos de archivos de maria
   └─ ...
```

---

## 6️⃣ Tabla de Funciones y Módulos

```
╔══════════════════════╦════════════════════╦═════════════════════════════════╗
║ FUNCIÓN              ║ MÓDULO             ║ QUÉ HACE                        ║
╠══════════════════════╬════════════════════╬═════════════════════════════════╣
║ hashear_contraseña   ║ auth.py            ║ PBKDF2-SHA256 + salt aleatorio  ║
║ verificar_contraseña ║ auth.py            ║ Compara contraseña con hash     ║
║ generar_token        ║ auth.py            ║ Crea UUID único                 ║
║ obtener_usuario_del  ║ auth.py            ║ Busca usuario por token         ║
║  _token              ║                    ║                                 ║
║ requiere_admin       ║ auth.py            ║ Lanza 403 si no es admin        ║
╠══════════════════════╬════════════════════╬═════════════════════════════════╣
║ LoggingMiddleware    ║ gateway.py         ║ Registra tiempo/código HTTP     ║
║ validar_carga        ║ gateway.py         ║ Valida PDF + tamaño             ║
╠══════════════════════╬════════════════════╬═════════════════════════════════╣
║ clasificar_con_      ║ consensus.py       ║ Distribuye a workers y calcula  ║
║  consenso            ║                    ║ mayoría                         ║
║ enviar_a_worker      ║ consensus.py       ║ POST a worker + manejo errores  ║
╠══════════════════════╬════════════════════╬═════════════════════════════════╣
║ construir_áreas_     ║ adapter.py         ║ Lista plana de áreas/subáreas   ║
║  planas              ║                    ║                                 ║
║ resolver_area        ║ adapter.py         ║ Mapea predicción a jerarquía    ║
║ adaptar_respuesta    ║ adapter.py         ║ Formatea JSON de /upload        ║
║  _carga              ║                    ║                                 ║
║ adaptar_respuesta    ║ adapter.py         ║ Formatea JSON de /files         ║
║  _archivos           ║                    ║                                 ║
╚══════════════════════╩════════════════════╩═════════════════════════════════╝
```

---

## 7️⃣ Estados y Códigos HTTP

```
┌────────────────────────────────────────────────────────────────┐
│ CÓDIGOS DE ÉXITO                                               │
├────────────────────────────────────────────────────────────────┤
│ 200 OK           → Operación exitosa                           │
│ 201 Created      → Recurso creado                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ ERRORES DEL CLIENTE                                            │
├────────────────────────────────────────────────────────────────┤
│ 400 Bad Request        → Validación fallida                    │
│                          ├─ No es PDF                           │
│                          ├─ Usuario existe                      │
│                          ├─ Contraseña < 6 chars              │
│                          └─ Parámetros faltantes               │
│                                                                │
│ 401 Unauthorized       → Autenticación fallida                │
│                          ├─ Token inválido                     │
│                          ├─ Token expirado                     │
│                          └─ Contraseña incorrecta              │
│                                                                │
│ 403 Forbidden          → Autorización fallida                 │
│                          └─ No es admin                        │
│                                                                │
│ 404 Not Found          → Recurso no encontrado                │
│                          ├─ Usuario no existe                  │
│                          ├─ Archivo no existe                  │
│                          └─ Área no existe                     │
│                                                                │
│ 413 Payload Too Large  → Archivo > 10 MB                      │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ ERRORES DEL SERVIDOR                                           │
├────────────────────────────────────────────────────────────────┤
│ 500 Internal Error     → Error no previsto                     │
│ 503 Service Unavailable → Workers no disponibles              │
│                          └─ Ningún node responde               │
└────────────────────────────────────────────────────────────────┘
```

---

## 8️⃣ Ciclo de Vida de un Documento

```
┌─────────────────┐
│  Usuario sube   │
│  PDF: paper.pdf │
└────────┬────────┘
         │ POST /upload
         ▼
    ┌────────────┐
    │ VALIDACIÓN │
    │ ✓ PDF OK   │
    │ ✓ < 10 MB  │
    └────────┬───┘
             │
             ▼
    ┌────────────────────────────┐
    │ CLASIFICACIÓN (CONSENSO)   │
    │ Node1: "Redes"             │
    │ Node2: "Redes"             │  → max: "Redes"
    │ Node3: "Seguridad"         │
    └────────┬───────────────────┘
             │
             ▼
    ┌──────────────────────┐
    │ RESOLUCIÓN ÁREA      │
    │ predicho = "Redes"   │
    │ area = "Redes"       │
    │ subarea = ""         │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────────────────┐
    │ REPLICACIÓN                      │
    │ node1: storage/node1/juan/Redes/ │
    │ node2: storage/node2/juan/Redes/ │
    │ node3: storage/node3/juan/Redes/ │
    └────────┬─────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────┐
    │ PERSISTENCIA                     │
    │ metadata/users/juan.json:        │
    │ {                                │
    │   "files": [{                    │
    │     "name": "paper.pdf",         │
    │     "area": "Redes",             │
    │     "subarea": "",               │
    │     "nodes": [1, 2, 3],          │
    │     "votos": {...}               │
    │   }]                             │
    │ }                                │
    └────────┬─────────────────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ RESPUESTA (200 OK)  │
    │ {                   │
    │   "archivo": "...", │
    │   "area": "Redes",  │
    │   "consenso": {...} │
    │ }                   │
    └─────────────────────┘


    AHORA EL ARCHIVO ESTÁ:
    ✓ Clasificado en 3 workers
    ✓ Replicado en 3 nodos (tolerancia a fallos)
    ✓ Registrado en metadatos
    ✓ En la jerarquía del usuario
    ✓ Listo para descargar/eliminar
```

---

## 9️⃣ Matriz de Dependencias

```
┌────────────┐
│ main.py    │  ← Punto de entrada (orquestador)
└─────┬──────┘
      │
      ├─→ auth.py
      │   ├─ hashlib (stdlib)
      │   ├─ uuid (stdlib)
      │   └─ FastAPI.HTTPException
      │
      ├─→ gateway.py
      │   ├─ FastAPI
      │   ├─ Starlette
      │   └─ time (stdlib)
      │
      ├─→ consensus.py
      │   ├─ requests
      │   ├─ json (stdlib)
      │   └─ FastAPI.HTTPException
      │
      ├─→ adapter.py
      │   └─ (sin dependencias externas)
      │
      └─→ database.py
          └─ supabase (Fase 4)


DEPENDENCIAS EXTERNAS (requirements.txt):
├─ fastapi          → Framework REST
├─ uvicorn          → ASGI server
├─ requests         → HTTP client (workers)
├─ python-multipart → Upload files
└─ (supabase)       → FASE 4
```

---

## 🔟 Resumen de Responsabilidades

```
┌────────────────────────────────────────────────────────────────┐
│ RESPONSABILIDAD         │ MÓDULO           │ FUNCIÓN            │
├────────────────────────────────────────────────────────────────┤
│ Seguridad (contraseña)  │ auth.py          │ hashear_*          │
│ Seguridad (token)       │ auth.py          │ generar_token      │
│ Validación (formato)    │ gateway.py       │ validar_carga      │
│ Monitoreo (logs)        │ gateway.py       │ LoggingMiddleware  │
│ Distribuición (workers) │ consensus.py     │ clasificar_*       │
│ Mapeo (jerarquía)       │ adapter.py       │ resolver_area      │
│ Formateo (JSON)         │ adapter.py       │ adaptar_respuesta  │
│ Persistencia (JSON)     │ main.py          │ cargar/guardar     │
│ Persistencia (BD)       │ database.py      │ (Fase 4)           │
│ Orquestación (todo)     │ main.py          │ endpoints          │
└────────────────────────────────────────────────────────────────┘
```

---

## 📌 Conceptos Clave

### 🔐 PBKDF2-SHA256 (Password-Based Key Derivation Function)
```
Entrada:     "MiPassword123"
             + salt aleatorio 16 bytes
             + 100,000 iteraciones SHA256

Proceso:     ┌─ Iteración 1:   hash1 = SHA256(pwd + salt)
             ├─ Iteración 2:   hash2 = SHA256(hash1)
             ├─ ...
             └─ Iteración 100k: hashFinal

Salida:      "salt_hex$hash_hex"

Ventajas:
├─ Lento (dificulta fuerza bruta)
├─ Determinista (mismo pwd + salt = mismo hash)
├─ Irreversible (no se recupera pwd del hash)
└─ Salt único por usuario (mismas pwd → diferentes hash)
```

### 🤝 Consenso por Mayoría
```
3 workers clasifican un PDF:
  Node1 → "Redes"
  Node2 → "Redes"
  Node3 → "Seguridad"

Votos: {"Redes": 2, "Seguridad": 1}
Ganador: "Redes" (mayoría)

Tolerancia a fallos:
├─ Si 1 falla: 2 votos válidos (50% > 0 votos fallidos)
├─ Si 2 fallan: 1 voto válido (100% pero no hay mayoría real)
└─ Si 3 fallan: 503 Service Unavailable
```

### 📊 Jerarquía de 2 Niveles
```
Nivel 1 (Temáticas):
  Redes, Seguridad, General, ...

Nivel 2 (Subtemáticas):
  Bajo "Redes": Protocolos, Topologías, WiFi, ...
  Bajo "Seguridad": Criptografía, Firewalls, ...
  Bajo "General": (siempre vacía)

Máxima flexibilidad:
├─ Documentos pueden ir al nivel 1 (sin subárea)
├─ Documentos pueden ir al nivel 2 (con subárea)
└─ Usuarios pueden crear su propia jerarquía
```

