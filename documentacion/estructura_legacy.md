# Estructura del Proyecto

Este documento define la estructura oficial de carpetas y responsabilidades del sistema.

## Estructura base

```text
clasificador-final/
â”œâ”€â”€ master/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ routes.py
â”‚   â”œâ”€â”€ auth.py
â”‚   â”œâ”€â”€ gateway.py
â”‚   â”œâ”€â”€ consensus.py
â”‚   â”œâ”€â”€ adapter.py
â”‚   â”œâ”€â”€ database.py
â”‚   â”œâ”€â”€ deletion_coordinator.py
â”‚   â””â”€â”€ apa.py
â”œâ”€â”€ worker/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ extractor.py
â”‚   â”œâ”€â”€ classifier.py
â”‚   â””â”€â”€ sync.py
â”œâ”€â”€ shared/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ election.py
â”‚   â””â”€â”€ leader_db.py
â”œâ”€â”€ metadata/
â”‚   â””â”€â”€ (obsoleto: no usado para persistencia de negocio)
â”œâ”€â”€ storage/
â”‚   â”œâ”€â”€ node1/
â”‚   â”œâ”€â”€ node2/
â”‚   â””â”€â”€ node3/
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â””â”€â”€ README_FRONTEND.md
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ README.md
â””â”€â”€ CRONOGRAMA.md
```

## Responsabilidades por carpeta

- master: capa de API de negocio, seguridad y administracion.
- worker: ejecucion de tareas de procesamiento de archivos.
- shared: servicios reutilizables entre nodos, como liderazgo y coordinacion.
- metadata: carpeta legacy, sin uso en persistencia de negocio tras migracion a Supabase.
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

