# Indice General de Documentacion

Este indice organiza la documentacion tecnica y funcional del proyecto con la arquitectura actual.

## Ruta de lectura recomendada

1. resumen_arquitectura.md
2. integracion_cluster.md
3. arquitectura_tecnica.md
4. validacion_gateway.md
5. diagramas_arquitectura.md
6. CRONOGRAMA.md

## Documentos disponibles

- [README.md](README.md): vision general, instalacion y ejecucion
- [resumen_arquitectura.md](resumen_arquitectura.md): panorama de arquitectura y operaciones
- [integracion_cluster.md](integracion_cluster.md): interaccion entre master, worker y shared
- [arquitectura_tecnica.md](arquitectura_tecnica.md): detalle de modulos, endpoints y decisiones de implementacion
- [validacion_gateway.md](validacion_gateway.md): validaciones, flujo de carga y adaptacion de respuesta
- [diagramas_arquitectura.md](diagramas_arquitectura.md): diagramas de despliegue, secuencia y flujo
- [CRONOGRAMA.md](CRONOGRAMA.md): roadmap de trabajo por bloques
- [estructura_legacy.md](estructura_legacy.md): referencia de estructura de carpetas y responsabilidades
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
- Categorias: GET /categories
- Documentos: POST /upload, GET /files, GET /download, DELETE /document
- Admin: GET/POST/PUT/DELETE en /admin/users
- Cluster: GET /heartbeat, GET /leader, POST /election/start, POST /election/coordinator

## Mantenimiento de documentacion

Cuando cambie el comportamiento del sistema, actualizar:

1. arquitectura_tecnica.md
2. integracion_cluster.md
3. diagramas_arquitectura.md
4. README.md
5. CRONOGRAMA.md

