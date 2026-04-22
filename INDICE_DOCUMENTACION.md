# Indice General de Documentacion

Este indice organiza la documentacion tecnica y funcional del proyecto con la arquitectura actual.

## Ruta de lectura recomendada

1. RESUMEN_EJECUTIVO.md
2. DOCUMENTACION_INTEGRACION.md
3. DOCUMENTACION_TECNICA.md
4. DOCUMENTACION_GATEWAY.md
5. DIAGRAMAS_VISUALES.md
6. CRONOGRAMA.md

## Documentos disponibles

- [README.md](README.md): vision general, instalacion y ejecucion
- [RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md): panorama de arquitectura y operaciones
- [DOCUMENTACION_INTEGRACION.md](DOCUMENTACION_INTEGRACION.md): interaccion entre master, worker y shared
- [DOCUMENTACION_TECNICA.md](DOCUMENTACION_TECNICA.md): detalle de modulos, endpoints y decisiones de implementacion
- [DOCUMENTACION_GATEWAY.md](DOCUMENTACION_GATEWAY.md): validaciones, flujo de carga y adaptacion de respuesta
- [DIAGRAMAS_VISUALES.md](DIAGRAMAS_VISUALES.md): diagramas de despliegue, secuencia y flujo
- [CRONOGRAMA.md](CRONOGRAMA.md): roadmap de trabajo por bloques
- [MIGRACION_ESTRUCTURA.md](MIGRACION_ESTRUCTURA.md): referencia de estructura de carpetas y responsabilidades
- [frontend/README_FRONTEND.md](frontend/README_FRONTEND.md): integracion del frontend con la API

## Mapa rapido de codigo

- [master/main.py](master/main.py): API principal y middleware de redireccion al lider
- [master/routes.py](master/routes.py): router reutilizable del nodo lider
- [worker/main.py](worker/main.py): procesamiento de PDF y rutas locales de nodo
- [shared/election.py](shared/election.py): eleccion de lider y heartbeat
- [shared/leader_db.py](shared/leader_db.py): persistencia del lider activo
- [master/consensus.py](master/consensus.py): clasificacion por mayoria de workers

## Endpoints centrales

- Auth: POST /register, POST /login, POST /logout
- Areas: GET /categories, POST /areas, POST /areas/{area}/sub
- Documentos: POST /upload, GET /files, GET /download, DELETE /document
- Admin: GET/POST/PUT/DELETE en /admin/users y /admin/areas
- Cluster: GET /heartbeat, GET /leader, POST /election/start, POST /election/coordinator

## Mantenimiento de documentacion

Cuando cambie el comportamiento del sistema, actualizar:

1. DOCUMENTACION_TECNICA.md
2. DOCUMENTACION_INTEGRACION.md
3. DIAGRAMAS_VISUALES.md
4. README.md
5. CRONOGRAMA.md
