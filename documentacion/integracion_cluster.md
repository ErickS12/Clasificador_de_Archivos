# Documentacion de Integracion

Este documento describe la integracion entre los modulos master, worker y shared.

## Vista general

```text
Cliente
  |
  v
master/main.py (lider)
  |- auth.py
  |- gateway.py
  |- consensus.py
  |- adapter.py
  |- routes.py
  |
  v
worker/main.py (nodos de proceso)
  |- extractor.py
  |- classifier.py

shared/
  |- election.py
  |- leader_db.py
```

## Integracion por flujo

### Autenticacion

1. register crea usuario.
2. login devuelve token.
3. middleware de seguridad aplica token en rutas protegidas.
4. requiere_admin valida operaciones administrativas.

### Clasificacion distribuida

1. upload valida archivo.
2. consensus envia PDF a workers.
3. workers procesan y responden area.
4. consensus calcula mayoria.
5. master guarda archivo y metadatos.
6. adapter construye respuesta final.

### Descarga y consistencia

1. cliente solicita download.
2. master consulta metadatos.
3. master busca archivo por nodos de storage.
4. devuelve archivo disponible.

### Liderazgo

1. cada nodo realiza heartbeat del lider.
2. ante falla, election inicia proceso Bully.
3. ganador actualiza [shared/leader_db.py](shared/leader_db.py).
4. middleware redirige peticiones al nuevo lider.

## Contratos entre modulos

- consensus <-> worker:
  - request: archivo + categorias permitidas
  - response: area clasificada

- election <-> leader_db:
  - lectura del lider actual
  - escritura del lider ganador
  - actualizacion de heartbeat

- main/routes <-> adapter:
  - normalizacion de payloads de respuesta para cliente

## Endpoints integrados

- Auth: /register, /login, /logout
- Categorias: /categories
- Documentos: /upload, /files, /download, /document
- Admin: /admin/users
- Cluster: /heartbeat, /leader, /election/start, /election/coordinator

## Dependencias de integracion

- FastAPI y Starlette para API y middleware
- Requests para comunicacion master-worker
- PyMuPDF para extraccion de texto
- scikit-learn para clasificacion
- Supabase client para estado de liderazgo

## Puntos de cierre tecnico

- completar borrado coordinado entre nodos
- completar sincronizacion de arranque en workers
- ampliar pruebas de recuperacion ante falla de nodo

