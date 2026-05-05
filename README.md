# Clasificador Distribuido de Archivos Científicos

Sistema distribuido para clasificación de PDFs científicos con FastAPI, consenso por mayoría entre nodos y elección de líder con algoritmo Bully.

## Arquitectura

```text
clasificador-final/
├── master/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── auth.py
│   ├── gateway.py
│   ├── consensus.py
│   ├── adapter.py
│   ├── database.py
│   ├── deletion_coordinator.py
│   └── apa.py
├── worker/
│   ├── __init__.py
│   ├── main.py
│   ├── extractor.py
│   ├── classifier.py
│   └── sync.py
├── shared/
│   ├── __init__.py
│   ├── election.py
│   └── leader_db.py
├── storage/
├── frontend/
├── requirements.txt
└── CRONOGRAMA.md
```

## Componentes clave

- líder (`master/`): API de negocio, autenticación, catálogo global, documentos y administración.
- nodos de procesamiento (`worker/`): procesamiento de PDF (extracción + clasificación).
- shared/election.py: detección de caída de líder y elección automática.
- shared/leader_db.py: registro del líder activo y heartbeat en Supabase.
- master/consensus.py: votación entre nodos para clasificación final.

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion local

Abrir 4 terminales desde la raiz. Cada proceso debe usar un `NODO_ID` distinto; el nodo con mayor ID disponible es el que puede quedar como lider si el actual cae:

```bash
# Inicia nodos de procesamiento (node1..node3)
uvicorn worker.main:app --port 5001
uvicorn worker.main:app --port 5002
uvicorn worker.main:app --port 5003
# Inicia el nodo con mayor prioridad (líder posible)
uvicorn master.main:app --port 8000
```

En desarrollo local no hace falta configurar nada más: si no defines variables de entorno, el sistema usa `localhost` por defecto.

Documentación OpenAPI:

```text
http://localhost:8000/docs
```

## Variables de entorno

- NODO_ID: id del nodo actual para elección de líder.
- CLUSTER_NODE_1_URL: URL real del nodo 1.
- CLUSTER_NODE_2_URL: URL real del nodo 2.
- CLUSTER_NODE_3_URL: URL real del nodo 3.
- CLUSTER_NODE_4_URL: URL real del nodo 4.
- CLUSTER_NODES_JSON: alternativa para definir todos los nodos en una sola variable JSON.
- SUPABASE_URL: URL del proyecto Supabase.
- SUPABASE_KEY: clave de acceso para operaciones de líder.
 - ALMACENAMIENTO_NODO: ruta local del nodo (p.ej. ../storage/node1). Mantiene nombre `ALMACENAMIENTO_NODO`.

## Configuración para 4 computadoras

Cuando el backend pase de local a una LAN con 4 PCs, el cambio real se hace en dos partes:

1. Cada máquina recibe una URL fija y un NODO_ID.
2. El backend deja de apuntar a localhost y usa esas URLs para elección, consenso y borrado.

### Mapa recomendado

| Máquina | NODO_ID | URL |
|---|---:|---|
| PC 1 | 1 | http://192.168.1.101:5001 |
| PC 2 | 2 | http://192.168.1.102:5002 |
| PC 3 | 3 | http://192.168.1.103:5003 |
| PC 4 | 4 | http://192.168.1.104:8000 |

### Opción A: configurar una variable por nodo

En cada computadora define el valor que le corresponde antes de iniciar FastAPI.

#### PowerShell

PC 1:
```powershell
$env:NODO_ID = "1"
$env:CLUSTER_NODE_1_URL = "http://192.168.1.101:5001"
$env:CLUSTER_NODE_2_URL = "http://192.168.1.102:5002"
$env:CLUSTER_NODE_3_URL = "http://192.168.1.103:5003"
$env:CLUSTER_NODE_4_URL = "http://192.168.1.104:8000"
uvicorn worker.main:app --host 0.0.0.0 --port 5001
```

PC 2:
```powershell
$env:NODO_ID = "2"
$env:CLUSTER_NODE_1_URL = "http://192.168.1.101:5001"
$env:CLUSTER_NODE_2_URL = "http://192.168.1.102:5002"
$env:CLUSTER_NODE_3_URL = "http://192.168.1.103:5003"
$env:CLUSTER_NODE_4_URL = "http://192.168.1.104:8000"
uvicorn worker.main:app --host 0.0.0.0 --port 5002
```

PC 3:
```powershell
$env:NODO_ID = "3"
$env:CLUSTER_NODE_1_URL = "http://192.168.1.101:5001"
$env:CLUSTER_NODE_2_URL = "http://192.168.1.102:5002"
$env:CLUSTER_NODE_3_URL = "http://192.168.1.103:5003"
$env:CLUSTER_NODE_4_URL = "http://192.168.1.104:8000"
uvicorn worker.main:app --host 0.0.0.0 --port 5003
```

PC 4:
```powershell
$env:NODO_ID = "4"
$env:CLUSTER_NODE_1_URL = "http://192.168.1.101:5001"
$env:CLUSTER_NODE_2_URL = "http://192.168.1.102:5002"
$env:CLUSTER_NODE_3_URL = "http://192.168.1.103:5003"
$env:CLUSTER_NODE_4_URL = "http://192.168.1.104:8000"
uvicorn master.main:app --host 0.0.0.0 --port 8000
```

### Opción B: definir todo en una sola variable

```powershell
$env:NODO_ID = "2"
$env:CLUSTER_NODES_JSON = '[{"id":1,"url":"http://192.168.1.101:5001"},{"id":2,"url":"http://192.168.1.102:5002"},{"id":3,"url":"http://192.168.1.103:5003"},{"id":4,"url":"http://192.168.1.104:8000"}]'
uvicorn worker.main:app --host 0.0.0.0 --port 5002
```

### Regla importante

- El `NODO_ID` debe coincidir con la máquina donde corre el proceso.
- La URL de cada nodo debe ser accesible desde las otras PCs.
- Si una PC cambia de IP, actualiza la configuración del cluster.
- Para pruebas en una sola laptop, no configures nada: el sistema sigue usando `localhost`.

## Endpoints principales

- Auth: /register, /login, /logout
- Categorías: /categories
- Documentos: /upload, /files, /download, /document
- Admin: /admin/users
- Elección de líder: /heartbeat, /leader, /election/start, /election/coordinator

## Flujo funcional

1. Usuario autentica y obtiene token.
2. Líder valida archivo y metadatos.
3. Líder envía el PDF a nodos y calcula mayoría.
4. PDF se replica en storage/node1-node3.
5. Metadatos y sesión se guardan en Supabase (tablas usuarios, tokens_sesion, tematicas, subtematicas, documentos, nodos_almacenamiento y consenso_votos).
6. Si el líder cae, cualquier nodo puede asumir el rol, siempre que tenga el `NODO_ID` correcto y gane la elección Bully.

## Documentación complementaria

- CRONOGRAMA.md
- documentacion/resumen_arquitectura.md
- documentacion/indice_documentacion.md
- documentacion/arquitectura_tecnica.md
- documentacion/integracion_cluster.md
- documentacion/validacion_gateway.md


