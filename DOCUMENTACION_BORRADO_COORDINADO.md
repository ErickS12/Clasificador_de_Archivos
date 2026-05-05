Documentación Completa: Borrado Distribuido con Eventual Consistency
══════════════════════════════════════════════════════════════════════════════════

VERSIÓN: 2.2 — OPCIÓN A (Eventual Consistency) + PUSH PATTERN + COLA ASÍNCRONA
ESTADO: ✅ COMPLETAMENTE IMPLEMENTADO
FASES: 5 (borrado en 2 pasos) + 6 (sincronización al startup) + 6b (push pattern) + 6c (cola asíncrona)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROPÓSITO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Implementar un patrón de "Consistencia Eventual" que garantiza:
  ✓ Archivos NUNCA quedan huérfanos cuando un nodo se cae
  ✓ Usuario NUNCA se bloquea esperando nodos offline
  ✓ Sincronización AUTOMÁTICA cuando el nodo se levanta
  ✓ Tolerancia a fallos transitorios (network, diskspace, permisos)


COLA ASÍNCRONA DE BORRADO
─────────────────────────

El usuario no espera al borrado real:
  → El sistema guarda la solicitud en una cola interna
  → Responde rápido con HTTP 202 Accepted
  → Un proceso en background ejecuta el borrado cuando haya condiciones disponibles
  → Si no hay suficientes nodos en ese momento, la solicitud se mantiene en cola


EL PROBLEMA ORIGINAL
────────────────────

Si intentábamos borrar un archivo y el Nodo 3 estaba offline:
  ✓ Nodo 1: archivo borrado OK
  ✓ Nodo 2: archivo borrado OK
  ✗ Nodo 3: timeout (offline/sin internet)

Con ALL-OR-NOTHING (rechazado):
  → NO se borra nada en Supabase
  → Usuario ve "error"
  → Nodo 3 sigue offline indefinidamente
  → Archivo 3 queda huérfano para siempre

Con EVENTUAL CONSISTENCY (implementado):
  → Se borra en Supabase SI 2+ de 3 resultados son exitosos
  → Usuario ve "eliminado" (ilusión de inmediatez)
  → Se crea registro en 'borrados_pendientes' para Nodo 3
  → Cuando Nodo 3 se levanta → sincroniza automáticamente
  → Archivo se limpia sin intervención manual


FLUJO EN TRES PASOS
───────────────────

PASO 1: BORRADO FÍSICO (paralelo en todos los nodos de procesamiento)
   Usuario presiona "Eliminar"
       ↓
  Líder envía POST /delete-files a node1, node2, node3
       ↓
   ✓ node1 → archivo borrado
   ✓ node2 → archivo borrado  
   ✗ node3 → timeout (offline)
       ↓
   resultados = {"node1": True, "node2": True, "node3": False}
   nodos_fallidos = ["node3"]


PASO 2: BORRADO LÓGICO EN BD (si 2+ exitosos)
   Chequea: ¿exitosos >= 2?
       ✓ SÍ → Continúa con el borrado real
       ✗ NO (solo 1 o 0) → La solicitud queda en cola y se reintenta después
       → El usuario NO ve error: recibe HTTP 202 Accepted
       → No se ejecuta el borrado en ese momento
       → El proceso en background volverá a intentar cuando haya capacidad suficiente
       ↓
   DELETE FROM documentos WHERE id=X
   ON DELETE CASCADE limpia automáticamente:
     - nodos_almacenamiento
     - consenso_votos
       ↓
   Usuario ya ve "eliminado" ✓
   (aunque node3 aún tiene copia huérfana)


PASO 3: SINCRONIZACIÓN EVENTUAL (cuando node3 se levanta)
   node3 inicia → @app.on_event("startup")
       ↓
   [NUEVO] POST /node-startup al líder (patrón PUSH)
       ↓
   Líder responde:
     "Tienes estos borrados pendientes: [...]"
       ↓
   [NUEVO] sincronizar_borrados_pendientes(lista_previa=...)
   (No necesita leer de BD, ya tiene la lista del líder)
       ↓
   Para cada archivo en la lista:
     - Intenta borrar del disco
     - Si éxito → UPDATE estado='completado'
     - Si fallo → intentos_fallidos++
       ↓
   ✓ Sistema en consistencia total
   (Sincronización inmediata, no espera job periódico)


CRONOLOGÍA
──────────

t=0:00   Usuario presiona "Eliminar"
t=0:01   Líder envía DELETE a nodos
t=0:02   ✓ node1 OK, ✓ node2 OK, ✗ node3 timeout
t=0:03   registrar_borrados_pendientes("node3", ...)
t=0:04   DELETE FROM documentos (usuario ya ve "eliminado")
t=0:05   Retorna respuesta (estado: "éxito_parcial")

[Horas después...]

t=2:30   node3 se levanta
t=2:31   worker/main.py @app.on_event("startup")
t=2:32   [NUEVO] POST /node-startup al líder
t=2:33   Líder devuelve: {"borrados_pendientes": [...]} 
t=2:34   Nodo sincroniza inmediatamente
t=2:35   Archivo borrado del disco de node3
t=2:36   UPDATE estado='completado'
t=2:37   ✓ Sistema 100% sincronizado (sin esperar job periódico)


IMPLEMENTACIÓN DETALLADA
════════════════════════════════════════════════════════════════════════════════


1. TABLA BORRADOS_PENDIENTES (new)
───────────────────────────────────

CREATE TABLE IF NOT EXISTS borrados_pendientes (
    id                  UUID PRIMARY KEY,
    documento_id        UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    nodo_destino        VARCHAR(50) NOT NULL,  -- 'node1', 'node2', 'node3'
    lista_archivos      JSONB NOT NULL,        -- array de archivos
    estado              VARCHAR(50) DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente', 'completado', 'fallido')),
    intentos_fallidos   INT DEFAULT 0,
    ultimo_intento      TIMESTAMPTZ,
    creado_en           TIMESTAMPTZ DEFAULT now(),
    actualizado_en      TIMESTAMPTZ DEFAULT now()
);

CAMPOS:
  - estado: 'pendiente' (aún no sincronizado) | 'completado' ✓ | 'fallido' (alerta manual)
  - intentos_fallidos: contador de reintentos (stop en 3)
  - lista_archivos: array JSON completo para poder borrar sin otra BD query


EJEMPLO DE REGISTRO:
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "documento_id": "660e8400-...",
    "nodo_destino": "node3",
    "lista_archivos": [{
      "nombre_usuario": "erick",
      "area": "Redes",
      "subarea": "Protocolos",
      "nombre": "paper.pdf"
    }],
    "estado": "pendiente",
    "intentos_fallidos": 0,
    "creado_en": "2026-05-02T10:20:00Z",
    "actualizado_en": "2026-05-02T10:20:00Z"
  }


2. master/deletion_coordinator.py
──────────────────────────────────

NUEVA FIRMA:
  solicitar_borrado_fisico(lista_archivos) 
    → (resultados_dict, nodos_fallidos_list)

LÓGICA MEJORADA:
  - Reintenta cada nodo hasta 3 veces
  - Retorna qué nodos fallaron
  - Sin lanzar excepción inmediatamente


NUEVA FUNCIÓN:
  registrar_borrados_pendientes(documento_id, nodos_fallidos, lista_archivos)
    → crea registros en BD para cada nodo que falló


NUEVA LÓGICA EN confirmar_y_purgar_base_datos:
  
  ANTES (all-or-nothing):
    if not all(resultados.values()):
        raise HTTPException(503, ...)
  
  AHORA (eventual consistency):
    exitosos = sum(1 for v in resultados.values() if v)
    if exitosos >= 2:  # 2+ de 3 = éxito
        DELETE FROM documentos  # AHORA
        registrar_borrados_pendientes()  # para los que fallaron
    else:
        raise HTTPException(503, ...)  # insuficientes


3. shared/sync.py (NEW FILE)
─────────────────────────────

FUNCIÓN 1: sincronizar_borrados_pendientes()
  Ejecutada: al @app.on_event("startup") de cada nodo
  
  Flujo:
    1. SELECT FROM borrados_pendientes WHERE estado='pendiente' AND nodo_destino=MY_NODE
    2. Para cada registro:
       - Para cada archivo en lista_archivos:
         * Intenta borrar del disco
       - Si todos borrados → UPDATE estado='completado'
       - Si alguno falla → intentos_fallidos++
       - Si intentos_fallidos > 3 → UPDATE estado='fallido'
  
  Retorna:
    {
      "completados": ["id1", "id2"],
      "fallidos": ["id3"],
      "reintentos": [{"id": "id4", "intentos": 2}],
      "timestamp": "..."
    }


FUNCIÓN 2: reintentar_borrados_periodicos()
  Job periódico de respaldo cada 5 minutos.
  Convive con el patrón PUSH: el nodo notifica al líder al levantarse.
  
  Beneficio:
    - El patrón PUSH sincroniza de inmediato al startup.
    - El job periódico recupera pendientes ante fallos transitorios.
  
  Fallback: Si líder offline, el nodo sincroniza localmente desde BD


FUNCIÓN 3: limpiar_borrados_completados()
  Uso: opcional, cleanup manual
  
  Elimina registros completados >7 días
  Evita crecimiento indefinido de tabla


3.5. cola_borrados (nueva cola asíncrona)
────────────────────────────────────────

TABLA:
  - documento_id: UUID del documento a borrar
  - usuario_id: UUID del usuario que solicitó el borrado
  - nombre_usuario: nombre visible del usuario
  - nombre_archivo: archivo solicitado
  - area / subarea: ubicación lógica del documento
  - estado: pendiente | procesando | completado | fallido
  - intentos: número de reintentos del proceso en background
  - ultimo_error: último motivo de fallo interno

RESPUESTA AL USUARIO:
  HTTP 202 Accepted
  {
    "estado": "aceptada",
    "mensaje": "Solicitud de borrado encolada",
    "cola_id": "uuid",
    "documento_id": "uuid"
  }


4. worker/main.py
──────────────────

NUEVOS IMPORTS:
  import requests
  from shared.sync import sincronizar_borrados_pendientes


NUEVOS EVENTOS:
  @app.on_event("startup")
  async def evento_inicio():
      iniciar_eleccion(app)
    asyncio.create_task(sincronizar_con_lider_al_startup())

  async def sincronizar_con_lider_al_startup():
    """Patrón PUSH: Nodo notifica al líder cuando se levanta"""
      try:
      # 1. Notificar al líder
          resp = requests.post(
        f"{LEADER_URL}/node-startup",
              json={"node_name": NOMBRE_NODO},
              timeout=5
          )
      # 2. Obtener lista de borrados del líder
          borrados = resp.json().get("borrados_pendientes", [])
          # 3. Sincronizar con la lista (patrón PUSH)
          await sincronizar_borrados_pendientes(lista_previa=borrados)
      except:
      # Fallback: sincronizar sin lista del líder
          await sincronizar_borrados_pendientes()


SALIDA ESPERADA AL INICIAR:
  [STARTUP-SYNC] Líder envió 2 borrados pendientes
  [SYNC] Patrón PUSH: Líder envió 2 borrados
  [SYNC] ✓ Borrado: ALMACENAMIENTO_NODO/erick/Redes/...
  [SYNC] ✓ Entrada 550e8400-... completada
  [SYNC] Resumen: 2 ✓, 0 ⟳, 0 ✗


5. master/routes.py
─────────────────────

[NUEVO] ENDPOINT: POST /node-startup
  Propósito: Que nodos notifiquen al líder cuando se levantan
  
  Entrada: {"node_name": "node1"}
  
  Salida: {
      "mensaje": "Node node1 registrado al startup",
      "borrados_pendientes": [
          {
              "id": "uuid",
              "lista_archivos": [{...}],
              "nodo_destino": "node1",
              "estado": "pendiente"
          }
      ],
      "timestamp": "2026-05-04T10:30:45Z"
  }

CAMBIO EN DELETE /document:

ANTES:
  resultados = solicitar_borrado_fisico(lista_archivos)
  confirmar_y_purgar_base_datos(documento["id"], resultados)
  return {"mensaje": "...", "nodos": resultados}

AHORA:
  resultados, nodos_fallidos = solicitar_borrado_fisico(lista_archivos)
  resumen = confirmar_y_purgar_base_datos(
      documento["id"],
      resultados,
      nodos_fallidos,
      lista_archivos
  )
  
  estado = "éxito_total" if not nodos_fallidos else "éxito_parcial"
  return {
      "mensaje": f"Archivo eliminado (estado: {estado})",
      "nodos": resultados,
      "estado": estado,
      "pendientes": resumen.get("ids_pendientes", []),
      "resumen": resumen,
  }


RESPUESTA AHORA INCLUYE:
  - estado: "éxito_total" | "éxito_parcial" | error (503)
  - pendientes: IDs de registros creados en BD
  - resumen: {"exitosos": 2, "fallidos": 1, "pendientes_creados": 1}


CASOS DE ÉXITO:

A) Éxito Total:
   HTTP 200
   {
     "estado": "éxito_total",
     "nodos": {"node1": true, "node2": true, "node3": true},
     "pendientes": [],
     "resumen": {"exitosos": 3, "fallidos": 0, "pendientes_creados": 0}
   }
   
   ✓ Todos los nodos borraron
   ✓ BD eliminada
   ✓ Sin archivos huérfanos


B) Éxito Parcial:
   HTTP 200
   {
     "estado": "éxito_parcial",
     "nodos": {"node1": true, "node2": true, "node3": false},
     "pendientes": ["550e8400-e29b-41d4-..."],
     "resumen": {"exitosos": 2, "fallidos": 1, "pendientes_creados": 1}
   }
   
   ✓ 2 de 3 borraron
   ✓ BD eliminada (usuario ve "eliminado")
   ✓ node3 se sincronizará cuando se levante


C) Fallo Total:
   HTTP 503
   {
    "detail": "Insuficientes nodos exitosos (0/3). Fallaron: ['node1', 'node2', 'node3']"
   }
   
   ✗ Menos de 2 exitosos
  ✗ BD NO se modifica en ese intento
  ✓ La solicitud queda en cola para reintento posterior


---

**Endpoint: Consultar estado de la solicitud en la cola**

GET /delete-requests/{cola_id}

Descripción:
- Permite al frontend consultar el estado de una solicitud en `cola_borrados`.
- Responde solo al usuario que creó la solicitud.

Respuesta de ejemplo:
{
  "cola_id": "550e8400-e29b-41d4-a716-446655440000",
  "documento_id": "660e8400-...",
  "estado": "pendiente",
  "intentos": 1,
  "ultimo_error": null,
  "creado_en": "2026-05-02T10:20:00Z",
  "actualizado_en": "2026-05-02T10:20:00Z"
}

Recomendación de UI (UX optimista):
- Al recibir `HTTP 202` tras `DELETE /document`, el frontend puede ocultar inmediatamente el PDF (optimistic hide) y mostrar una etiqueta "Borrado en proceso".
- Polling sugerido: consultar `GET /delete-requests/{cola_id}` cada 3–10s para confirmar el resultado final.
- Si `estado` pasa a `completado`: quitar el elemento definitivamente.
- Si `estado` pasa a `fallido`: mostrar alerta y ofrecer reintentar o restaurar la vista.

Snippet JS mínimo (fetch + polling):

```javascript
// Ejemplo simplificado
async function eliminarYEsperar(nombreArchivo, area, subarea){
  const resp = await fetch(`/document?nombre_archivo=${encodeURIComponent(nombreArchivo)}&area=${encodeURIComponent(area)}&subarea=${encodeURIComponent(subarea||'')}`, { method: 'DELETE', headers: { 'Authorization': 'Bearer '+token }});
  if(resp.status === 202){
    const body = await resp.json();
    const colaId = body.cola_id;
    // Ocultar visualmente
    ocultarElementoUI(nombreArchivo);
    mostrarBadge(nombreArchivo, 'Borrado en proceso');

    // Polling simple
    const interval = setInterval(async () => {
      const s = await fetch(`/delete-requests/${colaId}`, { headers: { 'Authorization': 'Bearer '+token }});
      if(s.status === 200){
        const status = await s.json();
        if(status.estado === 'completado'){
          clearInterval(interval);
          confirmarEliminacionUI(nombreArchivo);
        } else if(status.estado === 'fallido'){
          clearInterval(interval);
          mostrarError('El borrado falló. Intenta de nuevo o contacta soporte.');
          restaurarElementoUI(nombreArchivo);
        }
      }
    }, 5000);
  } else {
    const err = await resp.json();
    mostrarError(err.detail || 'Error en la solicitud de borrado.');
  }
}
```

Opcional: Para UX más fluida, sustituir polling por SSE o WebSocket para notificaciones push desde el líder cuando el estado cambie.


RESPUESTA ASÍNCRONA AL USUARIO:
  HTTP 202
  {
    "estado": "aceptada",
    "mensaje": "Solicitud de borrado encolada",
    "cola_id": "uuid",
    "documento_id": "uuid"
  }


GARANTÍAS
═════════════════════════════════════════════════════════════════════════════════

1. IDEMPOTENCIA
   ✓ Ejecutar sync 2 veces = mismo resultado
   ✓ No borra dos veces (archivo ya no existe = ok)
   ✓ No falla si el archivo ya desapareció (estado = "completado")


2. NO-DESTRUCTIVIDAD
   ✓ Si sincronización falla, archivo se deja en paz
  ✓ La solicitud queda en cola y el proceso en background reintenta automáticamente
   ✓ Después de 3 intentos → manual intervention (estado='fallido')


3. AUTOMATIZACIÓN
   ✓ Sin intervención manual (excepto 'fallido' después de 3 reintentos)
   ✓ Sincroniza automáticamente al startup
  ✓ Reintenta automáticamente en background mientras la cola siga pendiente


4. ESCALABILIDAD
   ✓ Funciona con 1 archivo o 1000 archivos
   ✓ Funciona con 3 nodos o 10 nodos
   ✓ Proporcional al número de archivos y nodos


5. CONSISTENCIA EVENTUAL
   ✓ TODOS los nodos TERMINARÁN con el mismo estado
   ✓ Garantizado al sincronizar (max ~1 hora, típicamente minutos)
   ✓ Sin data loss o corrupción


COMPARACIÓN: OPCIÓN A vs B
═════════════════════════════════════════════════════════════════════════════════

┌──────────────────┬────────────────────────┬────────────────────────┐
│ CRITERIO         │ OPCIÓN A (Elegida)     │ OPCIÓN B (Rechazada)   │
│                  │ Eventual Consistency   │ All-or-Nothing         │
├──────────────────┼────────────────────────┼────────────────────────┤
│ Usuario bloqueado │ ✗ NO (2+ = éxito)      │ ✓ SÍ (todos o nada)    │
│ UX                │ ✓ Muy buena            │ ✗ Pobre (esperas)      │
│ Resilencia        │ ✓ Excelente            │ ✗ Pobre                │
│ Huérfanos auto    │ ✓ Sí, al sync          │ ✗ No, forever          │
│ Complejidad       │ ⚠️ Media (3 pasos)     │ Simple (2 pasos)       │
│ Intervención      │ ✓ Mínima (auto)        │ ✓ Ninguna pero esperas │
└──────────────────┴────────────────────────┴────────────────────────┘


TESTING
═════════════════════════════════════════════════════════════════════════════════

TEST 1: ÉXITO TOTAL
  - 3 nodos activos
  - DELETE /document
  - Verificar: HTTP 200, estado='éxito_total', archivos no existen
  
TEST 2: ÉXITO PARCIAL
  - Detener nodo 3
  - DELETE /document
  - Verificar: HTTP 200, estado='éxito_parcial', pendiente creado
  - Levantar nodo 3
  - Verificar: nodo hace POST /node-startup
  - Verificar: archivo sincronizado INMEDIATAMENTE, estado='completado'
  - (No espera 5 minutos como antes)

TEST 3: FALLO TOTAL
  - Detener nodos 2 y 3
  - DELETE /document
  - Verificar: HTTP 503, archivo sigue existiendo en todos

TEST 4: PUSH PATTERN
  - Detener nodo 3 después de crear pendiente
  - Levantar nodo 3
  - Verificar logs: POST /node-startup al líder
  - Verificar: sincronización inmediata (patrón PUSH)
  - Verificar: archivo borrado en < 2 segundos


CONFIGURACIÓN PARA PRODUCCIÓN
═════════════════════════════════════════════════════════════════════════════════

1. Actualizar LEADER_URL en .env de cada nodo (fallback a MASTER_URL soportado):
  De: "http://localhost:8000"
  A:  "http://192.168.1.100:8000" (IP del líder en LAN)

2. Configurar ALMACENAMIENTO_NODO (rutas absolutas):
   De: "../storage/node1"
   A:  "/mnt/storage/node1" o "D:\\Documentos\\node1"

3. Crear .env en cada nodo con:
  NODE_NAME=node1  (o node2, node3)
  ALMACENAMIENTO_NODO=/mnt/storage/node1
  LEADER_URL=http://192.168.1.100:8000
  (Compatibilidad: el sistema seguirá leyendo WORKER_NODE_NAME y MASTER_URL si NODE_NAME o LEADER_URL no están definidos)
   SUPABASE_URL=https://...
   SUPABASE_KEY=...

4. Monitoreo:
   SELECT COUNT(*) FROM borrados_pendientes WHERE estado='fallido';
   → Si > 0: alerta automática
   
   SELECT COUNT(*) FROM borrados_pendientes WHERE estado='pendiente';
  → Si > 0 y llevan demasiado tiempo: revisar logs del líder/nodo


ESTADO FINAL
═════════════════════════════════════════════════════════════════════════════════

✅ FASE 5: Borrado en dos pasos — COMPLETADO
✅ FASE 6: Sincronización al startup — COMPLETADO
✅ FASE 6b: [OPTIMIZADO] Push Pattern en lugar de job periódico — COMPLETADO
✅ FASE 6c: Cleanup de registros antiguos — COMPLETADO

  ✅ FASE 7: Configuración para LAN (LISTA PARA IMPLEMENTAR)

El sistema ahora:
  ✅ Permite borrados parciales (2+ de 3)
  ✅ No bloquea al usuario
  ✅ Sincroniza automáticamente
  ✅ [NUEVO] Patrón PUSH: nodo notifica al líder al startup
  ✅ [NUEVO] Sincronización inmediata (~1 segundo)
  ✅ [ELIMINADO] Job periódico cada 5 minutos (ineficiente)
  ✅ Fallback automático si el líder está offline
  ✅ Previene archivos huérfanos
  ✅ Escalable y resiliente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Última actualización: 4 de mayo de 2026
Versión: 2.1 (Eventual Consistency + Push Pattern)
Estado: ✅ PRODUCCIÓN-LISTO


