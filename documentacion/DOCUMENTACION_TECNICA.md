# Documentacion Tecnica
# Clasificador Distribuido de Archivos Cientificos

## 1. Vision tecnica

La solucion se compone de tres dominios:

- master: coordinacion de negocio y exposicion de API
- worker: procesamiento de documentos
- shared: liderazgo y coordinacion de cluster

## 2. Estructura de modulos

```text
master/
  main.py
  routes.py
  auth.py
  gateway.py
  consensus.py
  adapter.py
  database.py
  deletion_coordinator.py
  apa.py

worker/
  main.py
  extractor.py
  classifier.py
  sync.py

shared/
  election.py
  leader_db.py
```

## 3. API principal

[master/main.py](master/main.py) contiene:

- inicializacion de app
- middlewares
- startup del cluster
- rutas de negocio

[master/routes.py](master/routes.py) permite reutilizar el mismo router cuando un worker asume liderazgo.

## 4. Seguridad

[master/auth.py](master/auth.py) implementa:

- hash de contrasena
- verificacion de credenciales
- tokens de sesion
- resolucion de usuario por token
- guardas de administracion

## 5. Gateway y validacion

[master/gateway.py](master/gateway.py) aporta:

- validar_carga: control de archivo entrante
- LoggingMiddleware: trazabilidad de peticiones

## 6. Consenso de clasificacion

[master/consensus.py](master/consensus.py):

- distribuye procesamiento a workers
- recolecta respuestas
- calcula mayoria
- degrada de forma controlada cuando un worker no responde

## 7. Adaptador de respuestas

[master/adapter.py](master/adapter.py) estandariza payloads para cliente.

## 8. Worker de procesamiento

[worker/main.py](worker/main.py) expone:

- POST /process: pipeline de extraccion y clasificacion
- POST /delete-files: interfaz de borrado coordinado

[worker/extractor.py](worker/extractor.py) usa PyMuPDF para extraer texto.
[worker/classifier.py](worker/classifier.py) aplica TF-IDF + LogisticRegression.

## 9. Liderazgo y disponibilidad

[shared/election.py](shared/election.py) implementa:

- heartbeat de lider
- deteccion de caida
- eleccion Bully
- publicacion de nuevo lider

[shared/leader_db.py](shared/leader_db.py) mantiene estado de lider activo en Supabase.

## 10. Persistencia y almacenamiento

- [master/database.py](master/database.py): capa de acceso a datos en Supabase
- Supabase: usuarios, sesiones, jerarquia, documentos, votos de consenso y nodos de replicacion
- [storage/node1](storage/node1), [storage/node2](storage/node2), [storage/node3](storage/node3): replicas de archivos

## 11. Endpoints disponibles

### Auth

- POST /register
- POST /login
- POST /logout

### Areas

- GET /categories
- POST /areas
- POST /areas/{area}/sub
- DELETE /areas/{area}
- DELETE /areas/{area}/sub/{subarea}

### Documentos

- POST /upload
- GET /files
- GET /download
- DELETE /document

### Admin

- GET /admin/users
- POST /admin/users
- PUT /admin/users/{nombre_usuario}
- DELETE /admin/users/{nombre_usuario}
- DELETE /admin/areas/{nombre_usuario}/{area}
- DELETE /admin/areas/{nombre_usuario}/{area}/{subarea}

### Cluster

- GET /heartbeat
- GET /leader
- POST /election/start
- POST /election/coordinator

## 12. Criterios de error

- 400/422: entrada invalida
- 401/403: autenticacion/permisos
- 404: recurso inexistente
- 503: indisponibilidad de servicio distribuido

## 13. Operacion recomendada

1. iniciar workers
2. iniciar nodo lider
3. validar /docs
4. ejecutar flujo register -> login -> upload -> files -> download

## 14. Pendientes de cierre tecnico

- consolidar borrado coordinado entre nodos
- consolidar sincronizacion de arranque en workers
- pruebas de resiliencia en entorno LAN
