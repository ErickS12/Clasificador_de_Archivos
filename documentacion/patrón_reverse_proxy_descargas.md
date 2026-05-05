# Patrón Reverse Proxy para Descargas Distribuidas

## 📋 Resumen Ejecutivo

El sistema de descarga ahora implementa un **patrón Reverse Proxy** que garantiza que los usuarios pueden descargar archivos desde cualquier dispositivo, sin importar en qué nodo del clúster esté almacenado el archivo.

**Problema que resuelve:**
- ❌ Antes: Si el Líder no tenía el PDF en su disco, la descarga fallaba
- ✅ Ahora: El Líder actúa como intermediario, pidiendo el archivo a otros nodos

---

## 🏗️ Arquitectura

### **Flujo de Descarga (Reverse Proxy)**

```
┌─────────────┐
│  Teléfono   │
│  Usuario    │
└──────┬──────┘
       │
       │ GET /download?archivo=paper.pdf&area=Redes
       ↓
   ┌────────────────────────────────┐
   │      LÍDER (Puerto 8000)        │
   │  ─ Valida autenticación         │
   │  ─ Consulta BD: ¿Quién tiene?   │
   │  ─ Actúa como intermediario     │
   └────────┬─────────────┬──────────┘
            │             │
    Intenta │             │ Si node1 falla,
     node1  │             │ intenta node2
            │             │
   ┌────────▼──┐    ┌─────▼────┐
   │  WORKER 1  │    │  WORKER 2 │
   │ (node1)    │    │ (node2)   │
   │ Puerto 5001│    │ Port 5002 │
   └────────────┘    └─────┬────┘
                            │
                            │ GET /serve-file
                            │ (Si tiene el archivo)
                            │
                   ┌────────▼──────────┐
                   │  Almacenamiento    │
                   │  node2/erick/...   │
                   │  paper.pdf ✅      │
                   └───────────────────┘
```

### **Componentes Principales**

#### 1. **Endpoint `/download` (Líder)** - `master/routes.py`
```python
GET /download?
    nombre_archivo=paper.pdf
    &area=Redes
    &subarea=Protocolos
```

**Responsabilidades:**
- ✅ Autenticar al usuario (requiere token JWT)
- ✅ Validar que el usuario sea propietario del archivo
- ✅ Consultar en Supabase qué nodos tienen el archivo
- ✅ Iterar por cada nodo disponible
- ✅ Hacer HTTP request a `/serve-file` del worker
- ✅ Streamear respuesta del worker al cliente
- ✅ Manejar errores (nodo caído, archivo no encontrado, timeout)

**Flujo detallado:**
```
1. Usuario solicita: GET /download?nombre_archivo=paper.pdf&area=Redes
2. Líder verifica token JWT → ✅ Usuario autenticado
3. Líder busca en BD: documentos WHERE usuario_id=? AND nombre_archivo=?
4. Líder valida que área/subárea existan
5. Líder consulta: SELECT * FROM nodos_almacenamiento WHERE documento_id=?
   Retorna: [
     {"nodo_id": 1, "nodo": "node1", "activo": true},
     {"nodo_id": 2, "nodo": "node2", "activo": true},
     {"nodo_id": 3, "nodo": "node3", "activo": true}
   ]
6. Líder itera por cada nodo:
   - Obtiene URL del nodo (ej: http://localhost:5002)
   - Hace HTTP GET: http://localhost:5002/serve-file?usuario=...&area=...&archivo=...
   - SI 200 OK: ✅ Streamea archivo al cliente → TERMINA
   - SI 404: Intenta siguiente nodo
   - SI timeout/error: Intenta siguiente nodo
7. SI ningún nodo responde: 503 Service Unavailable
```

**Códigos HTTP esperados:**
- `200 OK` - Archivo encontrado y entregado al cliente
- `404 Not Found` - Usuario no existe o archivo pertenece a otro usuario
- `503 Service Unavailable` - Todos los nodos están offline

---

#### 2. **Endpoint `/serve-file` (Workers)** - `worker/main.py`
```python
GET /serve-file?
    nombre_usuario=erick
    &area=Redes
    &subarea=Protocolos
    &nombre_archivo=paper.pdf
```

**Responsabilidades:**
- ✅ Recibir parámetros desde el Líder
- ✅ Construir ruta física al archivo
- ✅ Validar seguridad (prevenir path traversal)
- ✅ Servir el archivo si existe
- ✅ Retornar 404 si no existe

**Validación de Seguridad:**
```python
# Evitar ataques de path traversal
ruta_absoluta = os.path.abspath(ruta)
almacen_absoluto = os.path.abspath(ALMACENAMIENTO_NODO)

if not ruta_absoluta.startswith(almacen_absoluto):
    raise HTTPException(403, "Acceso denegado: ruta inválida")
    # Esto previene que alguien haga:
    # /serve-file?nombre_usuario=../../etc&archivo=passwd
```

**Estructura de carpetas esperada:**
```
storage/
├── node1/
│   └── erick/
│       └── Redes/
│           ├── Protocolos/
│           │   └── paper.pdf ✅
│           └── paper2.pdf ✅
├── node2/
│   └── maria/
│       └── IA/
│           └── neural_networks.pdf
└── node3/
    └── juan/
        └── Bases de Datos/
            └── sql_tutorial.pdf
```

**Códigos HTTP esperados:**
- `200 OK` - Archivo entregado
- `403 Forbidden` - Intento de path traversal
- `404 Not Found` - Archivo no existe en este nodo

---

## 🔄 Pasos Detallados del Flujo

### **Caso Exitoso: Archivo en node2**

```
T=0ms    Cliente → GET /download?archivo=paper.pdf&area=Redes
                   (Autenticado con JWT)

T=10ms   Líder: ✅ Token válido → usuario_id="abc123"

T=20ms   Líder: SELECT * FROM documentos 
                WHERE usuario_id='abc123' 
                AND nombre_archivo='paper.pdf'
                → Encontrado: documento_id="doc456"

T=30ms   Líder: SELECT * FROM nodos_almacenamiento
                WHERE documento_id='doc456'
                → [node1, node2, node3]

T=40ms   Líder: Intenta GET http://localhost:5001/serve-file?...
                → Timeout (node1 caído)

T=50ms   Líder: Intenta GET http://localhost:5002/serve-file?...
                → 200 OK ✅

T=60ms   Worker2: os.path.exists("/storage/node2/erick/Redes/paper.pdf")
                  → True ✅

T=70ms   Líder: Streamea bytes del archivo al cliente
                Content-Type: application/pdf
                Content-Disposition: attachment; filename=paper.pdf

T=200ms  Cliente: ✅ Recibe paper.pdf completamente
```

### **Caso de Error: Todos los nodos offline**

```
T=0ms    Cliente → GET /download?archivo=paper.pdf&area=Redes

T=20ms   Líder: ✅ Valida usuario y documento

T=30ms   Líder: SELECT nodos_almacenamiento...
                → [node1, node2, node3]

T=40ms   Líder: Intenta GET http://localhost:5001/serve-file?...
                → ConnectionError (nodo offline)

T=50ms   Líder: Intenta GET http://localhost:5002/serve-file?...
                → ConnectionError

T=60ms   Líder: Intenta GET http://localhost:5003/serve-file?...
                → ConnectionError

T=70ms   Líder: Retorna HTTP 503
                {
                  "detail": "Todos los nodos están offline. Reintenta en unos momentos."
                }

         Cliente: ❌ Error 503 Service Unavailable
```

---

## 📦 Imports y Dependencias

### **master/routes.py**
```python
import requests                              # Para HTTP requests a workers
import io                                    # Para streaming
from fastapi.responses import StreamingResponse  # Para enviar bytes al cliente
from shared.cluster_config import (
    obtener_nodos_cluster,                  # Obtener lista de nodos
    obtener_url_nodo                        # Obtener URL de un nodo específico
)
```

### **worker/main.py**
```python
from fastapi.responses import FileResponse   # Servir archivos
from fastapi import Query                    # Parámetros query
```

---

## 🛡️ Seguridad

### **Autenticación**
- ✅ Todas las descargas requieren JWT válido
- ✅ Solo el propietario del archivo puede descargarlo
- ✅ Token debe estar en header `Authorization: Bearer <token>`

### **Validación de Rutas (Path Traversal)**
El endpoint `/serve-file` en workers valida:
```python
ruta_absoluta = os.path.abspath(ruta)
almacen_absoluto = os.path.abspath(ALMACENAMIENTO_NODO)

if not ruta_absoluta.startswith(almacen_absoluto):
    raise HTTPException(403, "Acceso denegado")
```

**Esto previene ataques como:**
```
GET /serve-file?usuario=../../&archivo=../../../etc/passwd
→ HTTPException 403 Forbidden
```

### **Validaciones en Líder**
- ✅ Verifica que `usuario_id` sea propietario del documento
- ✅ Verifica que el documento esté en estado "activo" (no borrado)
- ✅ Verifica que área y subárea existan

---

## 🔧 Instalación y Configuración

### **Variables de Entorno Requeridas**
En `.env`:
```env
# Cluster config (ya existentes)
CLUSTER_NODES_JSON=[{"id": 1, "url": "http://localhost:5001"}, ...]
# O:
CLUSTER_NODE_1_URL=http://localhost:5001
CLUSTER_NODE_2_URL=http://localhost:5002
CLUSTER_NODE_3_URL=http://localhost:5003

# Almacenamiento
ALMACENAMIENTO_NODO=../storage/node1  # Diferente para cada worker
```

---

## 📊 Casos de Uso

### **Caso 1: Usuario descarga en mismo dispositivo**
```
Usuario sube PDF en Laptop 1
→ Se replica en Laptop 2, 3, 4 (3 copies)
→ Usuario descarga en Laptop 1
→ Líder le sirve desde Laptop 2 (Reverse Proxy)
```

### **Caso 2: Usuario descarga en dispositivo diferente**
```
Usuario sube PDF en Laptop 1 (nodo1)
→ Se replica en Laptop 2 (nodo2), Laptop 3 (nodo3)
→ Usuario se cambia a Teléfono
→ Teléfono pide descarga al Líder
→ Líder pide a Laptop 2 (nodo2)
→ Teléfono recibe el archivo ✅
```

### **Caso 3: Un nodo está caído**
```
Archivo está en: nodo1 (CAÍDO), nodo2, nodo3 (disponibles)
→ Líder intenta nodo1 → timeout
→ Líder intenta nodo2 → 200 OK ✅
→ Usuario recibe el archivo
```

---

## 🧪 Testing Manual

### **Paso 1: Crear archivo de prueba**
```bash
echo "PDF de prueba" > storage/node2/testuser/TestArea/test.pdf
```

### **Paso 2: Registrar en BD**
```sql
INSERT INTO documentos (usuario_id, nombre_archivo, tematica_id, estado)
VALUES ('user-uuid', 'test.pdf', 1, 'activo');

INSERT INTO nodos_almacenamiento (documento_id, nodo_id, activo)
VALUES ('doc-uuid', 2, true);  -- nodo2
```

### **Paso 3: Descargar**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/download?nombre_archivo=test.pdf&area=TestArea"
```

---

## ⚠️ Limitaciones Actuales

1. **Sin compresión**: Los PDFs se transmiten tal cual (sin gzip)
   - Solución futura: Agregar `Content-Encoding: gzip`

2. **Sin caché**: Cada descarga hace un request HTTP al worker
   - Solución futura: Implementar caché en Líder por tiempo limitado

3. **Sin resumible**: No soporta descargas resumibles (Range requests)
   - Solución futura: Agregar header `Accept-Ranges: bytes`

4. **Timeout fijo**: 10 segundos para conectar a workers
   - Configurable en línea: `respuesta = requests.get(..., timeout=10)`

---

## 📈 Rendimiento Esperado

| Métrica | Valor |
|---------|-------|
| Latencia Líder→Cliente | ~100-200ms (dependiendo de tamaño PDF) |
| Latencia HTTP Líder→Worker | ~10-50ms (localhost) |
| Velocidad de streaming | Limitada por red (TCP) |
| Timeout por nodo | 10 segundos |
| Max intentos | 3 nodos |

---

## 🔮 Mejoras Futuras

1. **Caché en Memoria**
   - Mantener últimos N archivos descargados en RAM del Líder
   - Evitar requests repetidos a workers

2. **Compresión**
   - Agregar gzip antes de streamear

3. **Range Requests**
   - Soportar descargas parciales (útil para videos)
   - Header: `Range: bytes=0-1000`

4. **Métricas**
   - Registrar tiempos de descarga
   - Identificar workers lentos

5. **Smart Load Balancing**
   - Priorizar workers cercanos (latencia baja)
   - Balancear carga entre nodos

---

## 📞 Referencias

- **Patrón Reverse Proxy**: https://en.wikipedia.org/wiki/Reverse_proxy
- **FastAPI Streaming**: https://fastapi.tiangolo.com/advanced/custom-response/
- **Requests Library**: https://requests.readthedocs.io/

