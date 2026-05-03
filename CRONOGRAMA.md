# Cronograma del Proyecto
# Clasificador Distribuido de Archivos Cientificos

Leyenda:
- Completo: funcional y validado en codigo
- En curso: funcional parcial o pendiente de cierre operativo
- Planificado: definido en roadmap

## Bloque A: Nucleo de Clasificacion Distribuida

Estado: Completo

- Worker de procesamiento PDF activo
- Extraccion de texto con PyMuPDF
- Clasificacion con TF-IDF + LogisticRegression
- Consenso por mayoria entre workers
- Replicacion de archivos en tres nodos

## Bloque B: API de Negocio y Seguridad

Estado: Completo

- Registro, login y logout
- Token Bearer para rutas protegidas
- Roles de usuario y administrador
- Gestion de areas y subareas
- CRUD administrativo de usuarios

## Bloque C: Alta Disponibilidad

Estado: En curso

- Eleccion de lider con algoritmo Bully
- Heartbeat y deteccion de caida
- Redireccion automatica al lider activo
- Registro de lider en Supabase
- Pendiente de cierre:
  - sincronizacion completa de arranque en workers
  - borrado coordinado en dos fases entre nodos

Nota de estado real: estas dos partes siguen solo diseñadas, no implementadas del todo en el codigo actual.

## Bloque D: Persistencia de Dominio

Estado: En curso

- Persistencia operativa principal en Supabase para usuarios, documentos y metadatos
- JSON sigue usandose solo como formato de transporte en algunas peticiones y respuestas, no como persistencia de negocio
- Persistencia de liderazgo en Supabase
- Plan de cierre:
  - capa completa de persistencia de negocio en base de datos
  - reglas de borrado relacional para consistencia

## Bloque E: Despliegue en Red LAN

Estado: Planificado

- Configuracion de IPs estaticas
- Sustitucion de endpoints locales por endpoints LAN
- Apertura de puertos en firewall
- Pruebas de tolerancia con nodos fisicos

## Bloque F: Frontend

Estado: En curso

- Estructura base de frontend presente en el proyecto
- Integracion completa de pantallas y flujo de usuario en roadmap

## Bloque G: Calidad y Cierre Operativo

Estado: Planificado

- Suite de pruebas end-to-end
- Verificacion de respuestas estandar
- Validacion de escenarios de falla y recuperacion
- Manual operativo y checklist de despliegue

## Resumen ejecutivo del cronograma

- Completos: Bloque A, Bloque B
- En curso: Bloque C, Bloque D, Bloque F
- Planificados: Bloque E, Bloque G

## Nota de interpretacion

Este cronograma es una guia historica. Para el estado real actual del sistema, priorizar el codigo fuente y el esquema de Supabase sobre estas notas.
