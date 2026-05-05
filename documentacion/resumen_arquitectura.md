# Resumen Ejecutivo
# Clasificador Distribuido de Archivos Cientificos

## Objetivo

Backend distribuido para clasificar documentos PDF por area tematica con alta disponibilidad y operacion por nodos.

## Arquitectura funcional

```text
Cliente
  |
  |- validacion y seguridad
  |- consenso de clasificacion
  |- gestion de metadatos en Supabase
  |- consenso de clasificacion
  |- gestion de metadatos
  |
  v
Workers de procesamiento
  |- extraccion de texto
  |- clasificacion

Servicios compartidos
  |- eleccion de lider (Bully)
  |- persistencia de lider (Supabase)
```

## Estado operativo

- Clasificacion distribuida: activa
- Consenso por mayoria: activo
- Redireccion al lider activo: activa
- Replicacion de archivos por nodos: activa
- Seguridad por token y roles: activa
- Persistencia de dominio en Supabase: activa

## Modulos principales

- [master/main.py](master/main.py): API principal y middleware
- [master/routes.py](master/routes.py): rutas reutilizables cuando un nodo asume liderazgo
- [master/consensus.py](master/consensus.py): votacion y resultado final de clasificacion
- [worker/main.py](worker/main.py): endpoint de procesamiento de PDF
- [worker/extractor.py](worker/extractor.py): extraccion de texto
- [worker/classifier.py](worker/classifier.py): modelo de clasificacion
- [shared/election.py](shared/election.py): heartbeat y eleccion de lider
- [shared/leader_db.py](shared/leader_db.py): registro de lider en Supabase

## Endpoints de negocio

- Auth: /register, /login, /logout
- Categorias: /categories
- Documentos: /upload, /files, /download, /document
- Admin: /admin/users

## Endpoints de cluster

- GET /heartbeat
- GET /leader
- POST /election/start
- POST /election/coordinator

## Flujo de clasificacion

1. Cliente envia PDF al nodo lider
2. Lider valida solicitud y permisos
3. Lider distribuye a workers
4. Workers responden area predicha
5. Lider calcula mayoria y responde
6. Documento y metadatos se registran

## Disponibilidad

- Si el lider cae, otro nodo asume liderazgo
- Si un worker no responde, el consenso continua con nodos disponibles
- El cliente puede resolver el lider actual via /leader

## Roadmap tecnico

- Cierre de borrado coordinado entre nodos
- Sincronizacion automatica de workers al inicio
- Despliegue en red LAN con IPs de produccion
- Integracion completa de frontend

## Conclusion

La base distribuida del sistema esta operativa, con separacion clara por responsabilidades y capacidad de evolucion hacia un despliegue de red completo.

