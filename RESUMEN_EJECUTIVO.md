# 🚀 Resumen Ejecutivo (5 minutos)

## ¿Qué es este proyecto?

Un **sistema distribuido de clasificación automática de PDFs científicos** que:
- Autentica usuarios con contraseñas seguras (PBKDF2)
- Organiza documentos en jerarquía temática (2 niveles)
- Distribuye trabajo entre 3 workers (clasificadores ML)
- Replica archivos en 3 nodos (tolerancia a fallos)
- Persiste datos en JSON (próximamente Supabase)

---

## 🏗️ Arquitectura en una Imagen

```
CLIENTE (Web/Mobile)
       ↓ HTTP REST
   MASTER (main.py) ← Aquí ocurre todo
       ├─→ auth.py (autenticación)
       ├─→ gateway.py (validación)
       ├─→ consensus.py (distribuye a workers)
       ├─→ adapter.py (mapea resultados)
       └─→ JSON files (persistencia)
       ↓
   3 WORKERS (localhost:5001-5003)
       ↓
   3 NODOS (storage/node1-3/)
```

---

## 📋 Los 5 Módulos Principales

| Módulo | Función | Ejemplo |
|--------|---------|---------|
| **auth.py** | Autenticación y seguridad | Hashear contraseña, generar token |
| **gateway.py** | Validación de entrada | Verificar que sea PDF, registrar logs |
| **consensus.py** | Distribuir trabajo a workers | Contactar 3 workers, calcular mayoría |
| **adapter.py** | Mapear y formatear datos | Resolver área en jerarquía, formatear JSON |
| **database.py** | Persistencia (Fase 4) | Aún no implementado (JSON actualmente) |

---

## 🔄 Flujo Principal: Subir un PDF

```
1. Usuario sube PDF con token JWT
   ↓
2. ¿Es válido el token?
   → No: 401 Unauthorized
   → Sí: continúa
   ↓
3. ¿Es un PDF válido? ¿< 10 MB?
   → No: 400 Bad Request / 413 Payload Too Large
   → Sí: continúa
   ↓
4. CONSENSO: Contactar 3 workers en paralelo
   Node1 → "Redes"
   Node2 → "Redes"
   Node3 → "Seguridad"
   → Ganador: "Redes" (mayoría)
   ↓
5. Mapear "Redes" a la jerarquía del usuario
   → ¿Existe como área?
   → ¿Existe como subárea?
   → Fallback: "General"
   ↓
6. Replicar PDF en 3 nodos
   storage/node1/usuario/Redes/pdf
   storage/node2/usuario/Redes/pdf
   storage/node3/usuario/Redes/pdf
   ↓
7. Guardar metadatos en JSON
   metadata/users/usuario.json
   ↓
8. Responder al cliente con 200 OK
   {
     "archivo": "paper.pdf",
     "area": "Redes",
     "replicado_en": ["node1", "node2", "node3"],
     "consenso": {...}
   }
```

---

## 🔐 Seguridad

### Contraseñas
```
Antes (Inseguro):        Después (Seguro):
usuarios.json:           usuarios.json:
password: "pwd123"       password_hash: "salt$hash"
                         
Cuando login:            Cuando login:
Compara string           1. Extrae salt del hash
directo ❌              2. Calcula PBKDF2(pwd, salt)
                        3. Compara hash nuevo con almacenado
                        4. PBKDF2 = lento (100k iteraciones)
                        5. Cada contraseña tiene salt único
```

### Tokens
```
Login exitoso → Genera UUID único
               → Almacena en session_token
               
Cada request → Header Authorization: Bearer <uuid>
              → Valida que UUID exista
              → Obtiene usuario del token
              → Si falla: 401 Unauthorized
```

### Roles
```
admin  → Puede crear/eliminar usuarios, forzar eliminación de áreas
user   → Solo puede gestionar sus propios archivos

Verificación: requiere_admin(datos_usuario)
             → Si role != "admin": 403 Forbidden
```

---

## 📁 Jerarquía de Archivos

```
Cada usuario puede crear su propia estructura:

Juan:
├─ Redes
│  ├─ Protocolos
│  │  └─ paper1.pdf, paper2.pdf
│  └─ Topologías
│     └─ paper3.pdf
├─ Seguridad
└─ General (siempre existe)
   └─ paper4.pdf (documentos sin clasificar)

María:
├─ IA
│  └─ Machine Learning
│     └─ paper5.pdf
└─ General
```

---

## 🤝 Consenso por Mayoría (¿Por qué 3 workers?)

```
Tolerancia a fallos:
├─ 1 falla: 2 votos válidos (2/3 es mayoría) ✓
├─ 2 fallan: 1 voto (no hay mayoría) → fallback a "General"
└─ 3 fallan: 503 Service Unavailable

Ejemplo:
Node1 → "Redes"
Node2 → "Redes"      } → Mayoría: "Redes"
Node3 → "Seguridad"

Si los 3 son diferentes:
Node1 → "Redes"
Node2 → "Seguridad"  } → No hay mayoría
Node3 → "IA"         → Fallback: "General"
```

---

## 💾 Dónde se Guardan los Datos

```
ARCHIVO USUARIOS:
./metadata/users.json
{
  "juan": {
    "password_hash": "salt$hash",
    "role": "admin",
    "session_token": "uuid-xxx",
    "areas": {
      "Redes": ["Protocolos", "Topologías"],
      "General": []
    }
  }
}

METADATOS DE ARCHIVOS:
./metadata/users/juan.json
{
  "files": [
    {
      "name": "paper.pdf",
      "area": "Redes",
      "subarea": "Protocolos",
      "nodes": ["node1", "node2", "node3"],
      "votos": {"node1": "Redes", ...},
      "version": 1
    }
  ]
}

ARCHIVOS REALES (REPLICADOS):
./storage/node1/juan/Redes/Protocolos/paper.pdf
./storage/node2/juan/Redes/Protocolos/paper.pdf
./storage/node3/juan/Redes/Protocolos/paper.pdf
```

---

## 🚀 Endpoints Principales

### Autenticación
```
POST /register
  → Crea usuario (primer usuario = admin)
  
POST /login
  → Devuelve token
  
POST /logout
  → Invalida token
```

### Documentos
```
POST /upload
  → Sube PDF, clasifica, replica, persiste
  → Respuesta: {archivo, area, replicado_en, consenso}
  
GET /files
  → Devuelve árbol de archivos clasificados
  
GET /download?archivo=pdf&area=Redes
  → Descarga archivo (prueba node1, node2, node3)
  
DELETE /document?archivo=pdf&area=Redes
  → Elimina de 3 nodos y metadatos
```

### Áreas
```
GET /categories
  → Devuelve jerarquía del usuario
  
POST /areas
  → Crea área nivel 1
  
POST /areas/{area}/sub
  → Crea subárea nivel 2
  
DELETE /areas/{area}
  → Elimina si está vacía
  
DELETE /areas/{area}/sub/{sub}
  → Elimina subárea si está vacía
```

### Admin
```
GET /admin/users
  → Lista todos los usuarios
  
POST /admin/users
  → Crea usuario (admin asigna rol)
  
DELETE /admin/users/{usuario}
  → Elimina usuario + sus archivos
  
PUT /admin/users/{usuario}
  → Modifica nombre o contraseña
  
DELETE /admin/areas/{usuario}/{area}
  → Elimina área aunque no esté vacía
  → Archivos se mueven a "General"
```

---

## 🔄 Relaciones entre Módulos

### Cuando sube un PDF (/upload):
```
main.py
  ├─→ gateway.validar_carga()       ← Valida PDF
  ├─→ adapter.construir_áreas_planas() ← Prepara para workers
  ├─→ consensus.clasificar_con_consenso() ← Distribuye trabajo
  │   └─→ requests.post(worker)     ← Contacta cada worker
  ├─→ adapter.resolver_area()       ← Mapea predicción
  ├─→ (replicación en storage/)     ← 3 nodos
  ├─→ (guardar metadatos)           ← JSON
  └─→ adapter.adaptar_respuesta_carga() ← Formatea respuesta
```

### Cuando autentica:
```
main.py
  ├─→ usuario_actual()
  │   └─→ auth.obtener_usuario_del_token()  ← Valida token
  └─→ requiere_admin()  (si es admin)
      └─→ auth.requiere_admin()
          └─→ Lanza 403 si no es admin
```

---

## 📊 Estados y Códigos HTTP

```
✓ 200 OK             → Todo bien
✓ 201 Created        → Recurso creado
❌ 400 Bad Request   → Validación fallida
❌ 401 Unauthorized  → Token inválido
❌ 403 Forbidden     → No es admin
❌ 404 Not Found     → Recurso no existe
❌ 413 Too Large     → PDF > 10 MB
❌ 503 Unavailable   → Workers caídos
```

---

## 🛣️ Roadmap

### ✅ Fase 1-3: COMPLETADO
- Autenticación con PBKDF2
- Validación de PDFs
- Consenso por mayoría
- Replicación en 3 nodos
- Persistencia en JSON

### 🔲 Fase 4: PENDIENTE
- Reemplazar JSON por **Supabase** (PostgreSQL)
- Tablas: usuarios, temáticas, documentos
- Más escalable y seguro

### 🔲 Fase 5+: FUTURO
- Frontend web (React/Vue)
- Integración con más modelos ML
- API Gateway
- Caché distribuido

---

## 🎯 Conclusión

**main.py es el director de orquesta que:**

1. **Autentica** usuarios (auth.py)
2. **Valida** solicitudes (gateway.py)
3. **Distribuye** trabajo a 3 workers (consensus.py)
4. **Mapea** resultados a jerarquía (adapter.py)
5. **Replica** en 3 nodos (tolerancia a fallos)
6. **Persiste** en JSON (pronto Supabase)
7. **Responde** al cliente (adapter.py)

Todos los módulos son especializados y reutilizables, facilitando testing y mantenimiento.

**El sistema es:**
- 🔒 Seguro (PBKDF2, tokens, roles)
- 📊 Confiable (consenso 3/3, replicación)
- 🚀 Escalable (modular, agnóstico a BD)
- 📝 Documentado (4 archivos de documentación)

