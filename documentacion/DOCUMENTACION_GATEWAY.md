# Documentacion de Gateway

## Proposito

El modulo [master/gateway.py](master/gateway.py) aplica controles de entrada y observabilidad sobre la API principal.

## Componentes

### validar_carga

Funcion encargada de validar archivos de entrada antes del procesamiento distribuido.

Validaciones clave:

- nombre de archivo presente
- extension PDF
- tamano permitido

Si la validacion falla, se devuelve HTTPException y la peticion no avanza al consenso.

### LoggingMiddleware

Middleware que registra informacion operativa por request:

- metodo HTTP
- ruta
- codigo de respuesta
- latencia

Este registro facilita monitoreo y diagnostico.

## Integracion en la aplicacion

El middleware se agrega en [master/main.py](master/main.py) junto con CORS y redireccion al lider.

Orden funcional:

1. redireccion al lider (cuando aplica)
2. CORS
3. logging
4. endpoint de negocio

## Flujo de upload

1. Cliente envia POST /upload.
2. validar_carga revisa archivo.
3. Si es valido, master invoca consenso.
4. Workers devuelven clasificacion.
5. Master calcula mayoria.
6. Se almacena archivo y metadatos.
7. Respuesta se adapta para cliente.
8. LoggingMiddleware registra resultado.

## Contrato de errores

- 400/422: entrada invalida
- 401/403: autenticacion o permisos
- 503: indisponibilidad de workers o lider

## Consideraciones operativas

- Mantener la validacion en borde evita carga innecesaria a workers.
- El logging no debe incluir datos sensibles.
- Ante errores de red, se recomienda incluir request-id para trazabilidad futura.

## Checklist de mantenimiento

- Revisar limites de tamano de archivo segun capacidad de nodos.
- Auditar formato y nivel de logs periodicamente.
- Alinear respuestas con [master/adapter.py](master/adapter.py) para mantener consistencia.
