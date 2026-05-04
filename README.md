# Clasificador Distribuido de Archivos Cientificos

Sistema distribuido para clasificacion de PDFs cientificos con FastAPI, consenso por mayoria entre workers y eleccion de lider con algoritmo Bully.

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
├── metadata/
├── storage/
├── frontend/
├── requirements.txt
└── CRONOGRAMA.md
```

## Componentes clave

- master: API de negocio, autenticacion, gestion de areas, documentos y administracion.
- worker: procesamiento de PDF (extraccion + clasificacion).
- shared/election.py: deteccion de caida de lider y eleccion automatica.
- shared/leader_db.py: registro del lider activo y heartbeat en Supabase.
- master/consensus.py: votacion entre workers para clasificacion final.

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion local

Abrir 4 terminales desde la raiz. Cada proceso debe usar un `NODO_ID` distinto; el nodo con mayor ID disponible es el que puede quedar como lider si el actual cae:

```bash
uvicorn worker.main:app --port 5001
uvicorn worker.main:app --port 5002
uvicorn worker.main:app --port 5003
uvicorn master.main:app --port 8000
```

En desarrollo local no hace falta configurar nada mas: si no defines variables de entorno, el sistema usa `localhost` por defecto.

Documentacion OpenAPI:

```text
http://localhost:8000/docs
```

## Variables de entorno

- NODO_ID: id del nodo actual para eleccion de lider.
- CLUSTER_NODE_1_URL: URL real del nodo 1.
- CLUSTER_NODE_2_URL: URL real del nodo 2.
- CLUSTER_NODE_3_URL: URL real del nodo 3.
- CLUSTER_NODE_4_URL: URL real del nodo 4.
- CLUSTER_NODES_JSON: alternativa para definir todos los nodos en una sola variable JSON.
- SUPABASE_URL: URL del proyecto Supabase.
- SUPABASE_KEY: clave de acceso para operaciones de lider.
- ALMACENAMIENTO_NODO: ruta local del nodo worker.

## Configuracion para 4 computadoras

Cuando el backend pase de local a una LAN con 4 PCs, el cambio real se hace en dos partes:

1. Cada maquina recibe una URL fija y un NODO_ID.
2. El backend deja de apuntar a localhost y usa esas URLs para election, consenso y borrado.

### Mapa recomendado

| Maquina | NODO_ID | URL |
|---|---:|---|
| PC 1 | 1 | http://192.168.1.101:5001 |
| PC 2 | 2 | http://192.168.1.102:5002 |
| PC 3 | 3 | http://192.168.1.103:5003 |
| PC 4 | 4 | http://192.168.1.104:8000 |

### Opcion A: configurar una variable por nodo

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

### Opcion B: definir todo en una sola variable

```powershell
$env:NODO_ID = "2"
$env:CLUSTER_NODES_JSON = '[{"id":1,"url":"http://192.168.1.101:5001"},{"id":2,"url":"http://192.168.1.102:5002"},{"id":3,"url":"http://192.168.1.103:5003"},{"id":4,"url":"http://192.168.1.104:8000"}]'
uvicorn worker.main:app --host 0.0.0.0 --port 5002
```

### Regla importante

- El `NODO_ID` debe coincidir con la maquina donde corre el proceso.
- La URL de cada nodo debe ser accesible desde las otras PCs.
- Si una PC cambia de IP, actualiza la configuracion del cluster.
- Para pruebas en una sola laptop, no configures nada: el sistema sigue usando `localhost`.

## Endpoints principales

- Auth: /register, /login, /logout
- Areas: /categories, /areas, /areas/{area}/sub
- Documentos: /upload, /files, /download, /document
- Admin: /admin/users, /admin/areas/*
- Eleccion de lider: /heartbeat, /leader, /election/start, /election/coordinator

## Flujo funcional

1. Usuario autentica y obtiene token.
2. Master valida archivo y metadatos.
3. Master envia el PDF a workers y calcula mayoria.
4. PDF se replica en storage/node1-node3.
5. Metadatos y sesion se guardan en Supabase (tablas usuarios, tokens_sesion, tematicas, subtematicas, documentos, nodos_almacenamiento y consenso_votos).
6. Si el lider cae, cualquier worker o el master puede asumir el rol, siempre que tenga el `NODO_ID` correcto y gane la eleccion Bully.

## Documentacion complementaria

- CRONOGRAMA.md
- RESUMEN_EJECUTIVO.md
- INDICE_DOCUMENTACION.md
- DOCUMENTACION_TECNICA.md
