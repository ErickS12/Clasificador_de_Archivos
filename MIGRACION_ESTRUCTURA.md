# Estructura del Proyecto

Este documento define la estructura oficial de carpetas y responsabilidades del sistema.

## Estructura base

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
│   ├── users.json
│   └── users/
├── storage/
│   ├── node1/
│   ├── node2/
│   └── node3/
├── frontend/
│   ├── src/
│   └── README_FRONTEND.md
├── requirements.txt
├── README.md
└── CRONOGRAMA.md
```

## Responsabilidades por carpeta

- master: capa de API de negocio, seguridad y administracion.
- worker: ejecucion de tareas de procesamiento de archivos.
- shared: servicios reutilizables entre nodos, como liderazgo y coordinacion.
- metadata: informacion de usuarios y metadatos de documentos.
- storage: replicas fisicas de los documentos por nodo.
- frontend: cliente web y su configuracion de consumo de API.

## Reglas de importacion

- Importaciones compartidas desde shared.
- Importaciones de dominio desde master y worker segun contexto.
- Evitar duplicar logica de cluster fuera de shared.

## Convencion de ejecucion

- Nodo lider: master.main:app
- Nodos de procesamiento: worker.main:app
- Configuracion de nodo por variables de entorno (NODO_ID, ALMACENAMIENTO_NODO)

## Criterios de organizacion

- Cada modulo tiene responsabilidad unica.
- Las rutas de negocio se centralizan en master/routes.py.
- El estado de liderazgo se mantiene fuera de la capa HTTP en shared.
- La documentacion tecnica y operativa se mantiene separada.
