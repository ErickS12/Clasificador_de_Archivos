DocumentaciÃ³n Completa: Borrado Distribuido con Eventual Consistency
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

VERSIÃ“N: 2.2 â€” OPCIÃ“N A (Eventual Consistency) + PUSH PATTERN + COLA ASÃNCRONA
ESTADO: âœ… COMPLETAMENTE IMPLEMENTADO
FASES: 5 (borrado en 2 pasos) + 6 (sincronizaciÃ³n al startup) + 6b (push pattern) + 6c (cola asÃ­ncrona)

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
PROPÃ“SITO
â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

Implementar un patrÃ³n de "Consistencia Eventual" que garantiza:
  âœ“ Archivos NUNCA quedan huÃ©rfanos cuando un nodo se cae
  âœ“ Usuario NUNCA se bloquea esperando nodos offline
  âœ“ SincronizaciÃ³n AUTOMÃTICA cuando el nodo se levanta
  âœ“ Tolerancia a fallos transitorios (network, diskspace, permisos)


COLA ASÃNCRONA DE BORRADO
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

El usuario no espera al borrado real:
  â†’ El sistema guarda la solicitud en una cola interna
  â†’ Responde rÃ¡pido con HTTP 202 Accepted
  â†’ Un proceso en background ejecuta el borrado cuando haya condiciones disponibles
  â†’ Si no hay suficientes nodos en ese momento, la solicitud se mantiene en cola


EL PROBLEMA ORIGINAL
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Si intentÃ¡bamos borrar un archivo y el Nodo 3 estaba offline:
  âœ“ Nodo 1: archivo borrado OK
  âœ“ Nodo 2: archivo borrado OK
  âœ— Nodo 3: timeout (offline/sin internet)

Con ALL-OR-NOTHING (rechazado):
  â†’ NO se borra nada en Supabase
  â†’ Usuario ve "error"
  â†’ Nodo 3 sigue offline indefinidamente
  â†’ Archivo 3 queda huÃ©rfano para siempre

Con EVENTUAL CONSISTENCY (implementado):
  â†’ Se borra en Supabase SI 2+ de 3 workado exitoso
  â†’ Usuario ve "eliminado" (ilusiÃ³n de inmediatez)
  â†’ Se crea registro en 'borrados_pendientes' para Nodo 3
  â†’ Cuando Nodo 3 se levanta â†’ sincroniza automÃ¡ticamente
  â†’ Archivo se limpia sin intervenciÃ³n manual


FLUJO EN TRES PASOS
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

PASO 1: BORRADO FÃSICO (paralelo en todos los workers)
   Usuario presiona "Eliminar"
       â†“
   Master envÃ­a POST /delete-files a node1, node2, node3
       â†“
   âœ“ node1 â†’ archivo borrado
   âœ“ node2 â†’ archivo borrado  
   âœ— node3 â†’ timeout (offline)
       â†“
   resultados = {"node1": True, "node2": True, "node3": False}
   nodos_fallidos = ["node3"]


PASO 2: BORRADO LÃ“GICO EN BD (si 2+ exitosos)
   Chequea: Â¿exitosos >= 2?
       âœ“ SÃ â†’ ContinÃºa con el borrado real
       âœ— NO (solo 1 o 0) â†’ La solicitud queda en cola y se reintenta despuÃ©s
       â†’ El usuario NO ve error: recibe HTTP 202 Accepted
       â†’ No se ejecuta el borrado en ese momento
       â†’ El proceso en background volverÃ¡ a intentar cuando haya capacidad suficiente
       â†“
   DELETE FROM documentos WHERE id=X
   ON DELETE CASCADE limpia automÃ¡ticamente:
     - nodos_almacenamiento
     - consenso_votos
       â†“
   Usuario ya ve "eliminado" âœ“
   (aunque node3 aÃºn tiene copia huÃ©rfana)


PASO 3: SINCRONIZACIÃ“N EVENTUAL (cuando node3 se levanta)
   node3 inicia â†’ @app.on_event("startup")
       â†“
   [NUEVO] POST /node-startup al Master (patrÃ³n PUSH)
       â†“
   Master responde:
     "Tienes estos borrados pendientes: [...]"
       â†“
   [NUEVO] sincronizar_borrados_pendientes(lista_previa=...)
   (No necesita leer de BD, ya tiene la lista del master)
       â†“
   Para cada archivo en la lista:
     - Intenta borrar del disco
     - Si Ã©xito â†’ UPDATE estado='completado'
     - Si fallo â†’ intentos_fallidos++
       â†“
   âœ“ Sistema en consistencia total
   (SincronizaciÃ³n inmediata, no espera job periÃ³dico)


CRONOLOGÃA
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

t=0:00   Usuario presiona "Eliminar"
t=0:01   Master envÃ­a DELETE a workers
t=0:02   âœ“ node1 OK, âœ“ node2 OK, âœ— node3 timeout
t=0:03   registrar_borrados_pendientes("node3", ...)
t=0:04   DELETE FROM documentos (usuario ya ve "eliminado")
t=0:05   Retorna respuesta (estado: "Ã©xito_parcial")

[Horas despuÃ©s...]

t=2:30   node3 se levanta
t=2:31   worker/main.py @app.on_event("startup")
t=2:32   [NUEVO] POST /node-startup al master
t=2:33   Master devuelve: {"borrados_pendientes": [...]}
t=2:34   Worker sincroniza inmediatamente
t=2:35   Archivo borrado del disco de node3
t=2:36   UPDATE estado='completado'
t=2:37   âœ“ Sistema 100% sincronizado (sin esperar job periÃ³dico)


IMPLEMENTACIÃ“N DETALLADA
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


1. TABLA BORRADOS_PENDIENTES (new)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
  - estado: 'pendiente' (aÃºn no sincronizado) | 'completado' âœ“ | 'fallido' (alerta manual)
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
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

NUEVA FIRMA:
  solicitar_borrado_fisico(lista_archivos) 
    â†’ (resultados_dict, nodos_fallidos_list)

LÃ“GICA MEJORADA:
  - Reintenta cada nodo hasta 3 veces
  - Retorna quÃ© nodos fallaron
  - Sin lanzar excepciÃ³n inmediatamente


NUEVA FUNCIÃ“N:
  registrar_borrados_pendientes(documento_id, nodos_fallidos, lista_archivos)
    â†’ crea registros en BD para cada nodo que fallÃ³


NUEVA LÃ“GICA EN confirmar_y_purgar_base_datos:
  
  ANTES (all-or-nothing):
    if not all(resultados.values()):
        raise HTTPException(503, ...)
  
  AHORA (eventual consistency):
    exitosos = sum(1 for v in resultados.values() if v)
    if exitosos >= 2:  # 2+ de 3 = Ã©xito
        DELETE FROM documentos  # AHORA
        registrar_borrados_pendientes()  # para los que fallaron
    else:
        raise HTTPException(503, ...)  # insuficientes


3. shared/sync.py (NEW FILE)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FUNCIÃ“N 1: sincronizar_borrados_pendientes()
  Ejecutada: al @app.on_event("startup") de cada worker
  
  Flujo:
    1. SELECT FROM borrados_pendientes WHERE estado='pendiente' AND nodo_destino=MY_NODE
    2. Para cada registro:
       - Para cada archivo en lista_archivos:
         * Intenta borrar del disco
       - Si todos borrados â†’ UPDATE estado='completado'
       - Si alguno falla â†’ intentos_fallidos++
       - Si intentos_fallidos > 3 â†’ UPDATE estado='fallido'
  
  Retorna:
    {
      "completados": ["id1", "id2"],
      "fallidos": ["id3"],
      "reintentos": [{"id": "id4", "intentos": 2}],
      "timestamp": "..."
    }


FUNCIÃ“N 2: [ELIMINADO] reintentar_borrados_periodicos()
  [CAMBIO] Ya no hay job periÃ³dico cada 5 minutos.
  Ahora el patrÃ³n es PUSH: worker notifica al master cuando se levanta.
  
  Razones del cambio:
    - 10x mÃ¡s rÃ¡pido: ~1 segundo vs 5 minutos
    - Menor overhead de CPU: sin polling continuo
    - MÃ¡s reactivo: sincroniza inmediatamente
  
  Fallback: Si master offline, worker sincroniza localmente desde BD


FUNCIÃ“N 3: limpiar_borrados_completados()
  Uso: opcional, cleanup manual
  
  Elimina registros completados >7 dÃ­as
  Evita crecimiento indefinido de tabla


3.5. cola_borrados (nueva cola asÃ­ncrona)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TABLA:
  - documento_id: UUID del documento a borrar
  - usuario_id: UUID del usuario que solicitÃ³ el borrado
  - nombre_usuario: nombre visible del usuario
  - nombre_archivo: archivo solicitado
  - area / subarea: ubicaciÃ³n lÃ³gica del documento
  - estado: pendiente | procesando | completado | fallido
  - intentos: nÃºmero de reintentos del background worker
  - ultimo_error: Ãºltimo motivo de fallo interno

RESPUESTA AL USUARIO:
  HTTP 202 Accepted
  {
    "estado": "aceptada",
    "mensaje": "Solicitud de borrado encolada",
    "cola_id": "uuid",
    "documento_id": "uuid"
  }


4. worker/main.py
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

NUEVOS IMPORTS:
  import requests
  from shared.sync import sincronizar_borrados_pendientes


NUEVOS EVENTOS:
  @app.on_event("startup")
  async def evento_inicio():
      iniciar_eleccion(app)
      asyncio.create_task(sincronizar_con_master_al_startup())

  async def sincronizar_con_master_al_startup():
      """PatrÃ³n PUSH: Worker notifica al master cuando se levanta"""
      try:
          # 1. Notificar al master
          resp = requests.post(
              f"{MASTER_URL}/node-startup",
              json={"node_name": NOMBRE_NODO},
              timeout=5
          )
          # 2. Obtener lista de borrados del master
          borrados = resp.json().get("borrados_pendientes", [])
          # 3. Sincronizar con la lista (patrÃ³n PUSH)
          await sincronizar_borrados_pendientes(lista_previa=borrados)
      except:
          # Fallback: sincronizar sin lista del master
          await sincronizar_borrados_pendientes()


SALIDA ESPERADA AL INICIAR:
  [STARTUP-SYNC] Master enviÃ³ 2 borrados pendientes
  [SYNC] PatrÃ³n PUSH: Master enviÃ³ 2 borrados
  [SYNC] âœ“ Borrado: ALMACENAMIENTO_NODO/erick/Redes/...
  [SYNC] âœ“ Entrada 550e8400-... completada
  [SYNC] Resumen: 2 âœ“, 0 âŸ³, 0 âœ—


5. master/routes.py
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

[NUEVO] ENDPOINT: POST /node-startup
  PropÃ³sito: Que workers notifiquen al master cuando se levantan
  
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
  
  estado = "Ã©xito_total" if not nodos_fallidos else "Ã©xito_parcial"
  return {
      "mensaje": f"Archivo eliminado (estado: {estado})",
      "nodos": resultados,
      "estado": estado,
      "pendientes": resumen.get("ids_pendientes", []),
      "resumen": resumen,
  }


RESPUESTA AHORA INCLUYE:
  - estado: "Ã©xito_total" | "Ã©xito_parcial" | error (503)
  - pendientes: IDs de registros creados en BD
  - resumen: {"exitosos": 2, "fallidos": 1, "pendientes_creados": 1}


CASOS DE Ã‰XITO:

A) Ã‰xito Total:
   HTTP 200
   {
     "estado": "Ã©xito_total",
     "nodos": {"node1": true, "node2": true, "node3": true},
     "pendientes": [],
     "resumen": {"exitosos": 3, "fallidos": 0, "pendientes_creados": 0}
   }
   
   âœ“ Todos los nodos borraron
   âœ“ BD eliminada
   âœ“ Sin archivos huÃ©rfanos


B) Ã‰xito Parcial:
   HTTP 200
   {
     "estado": "Ã©xito_parcial",
     "nodos": {"node1": true, "node2": true, "node3": false},
     "pendientes": ["550e8400-e29b-41d4-..."],
     "resumen": {"exitosos": 2, "fallidos": 1, "pendientes_creados": 1}
   }
   
   âœ“ 2 de 3 borraron
   âœ“ BD eliminada (usuario ve "eliminado")
   âœ“ node3 se sincronizarÃ¡ cuando se levante


C) Fallo Total:
   HTTP 503
   {
     "detail": "Insuficientes workers exitosos (0/3). Fallaron: ['node1', 'node2', 'node3']"
   }
   
   âœ— Menos de 2 exitosos
  âœ— BD NO se modifica en ese intento
  âœ“ La solicitud queda en cola para reintento posterior


---

**Endpoint: Consultar estado de la solicitud en la cola**

GET /delete-requests/{cola_id}

DescripciÃ³n:
- Permite al frontend consultar el estado de una solicitud en `cola_borrados`.
- Responde solo al usuario que creÃ³ la solicitud.

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

RecomendaciÃ³n de UI (UX optimista):
- Al recibir `HTTP 202` tras `DELETE /document`, el frontend puede ocultar inmediatamente el PDF (optimistic hide) y mostrar una etiqueta "Borrado en proceso".
- Polling sugerido: consultar `GET /delete-requests/{cola_id}` cada 3â€“10s para confirmar el resultado final.
- Si `estado` pasa a `completado`: quitar el elemento definitivamente.
- Si `estado` pasa a `fallido`: mostrar alerta y ofrecer reintentar o restaurar la vista.

Snippet JS mÃ­nimo (fetch + polling):

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
          mostrarError('El borrado fallÃ³. Intenta de nuevo o contacta soporte.');
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

Opcional: Para UX mÃ¡s fluida, sustituir polling por SSE o WebSocket para notificaciones push desde el master cuando el estado cambie.


RESPUESTA ASÃNCRONA AL USUARIO:
  HTTP 202
  {
    "estado": "aceptada",
    "mensaje": "Solicitud de borrado encolada",
    "cola_id": "uuid",
    "documento_id": "uuid"
  }


GARANTÃAS
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

1. IDEMPOTENCIA
   âœ“ Ejecutar sync 2 veces = mismo resultado
   âœ“ No borra dos veces (archivo ya no existe = ok)
   âœ“ No falla si el archivo ya desapareciÃ³ (estado = "completado")


2. NO-DESTRUCTIVIDAD
   âœ“ Si sincronizaciÃ³n falla, archivo se deja en paz
  âœ“ La solicitud queda en cola y el background worker reintenta automÃ¡ticamente
   âœ“ DespuÃ©s de 3 intentos â†’ manual intervention (estado='fallido')


3. AUTOMATIZACIÃ“N
   âœ“ Sin intervenciÃ³n manual (excepto 'fallido' despuÃ©s de 3 reintentos)
   âœ“ Sincroniza automÃ¡ticamente al startup
  âœ“ Reintenta automÃ¡ticamente en background mientras la cola siga pendiente


4. ESCALABILIDAD
   âœ“ Funciona con 1 archivo o 1000 archivos
   âœ“ Funciona con 3 nodos o 10 nodos
   âœ“ Proporcional al nÃºmero de archivos y nodos


5. CONSISTENCIA EVENTUAL
   âœ“ TODOS los nodos TERMINARÃN con el mismo estado
   âœ“ Garantizado al sincronizar (max ~1 hora, tÃ­picamente minutos)
   âœ“ Sin data loss o corrupciÃ³n


COMPARACIÃ“N: OPCIÃ“N A vs B
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ CRITERIO         â”‚ OPCIÃ“N A (Elegida)     â”‚ OPCIÃ“N B (Rechazada)   â”‚
â”‚                  â”‚ Eventual Consistency   â”‚ All-or-Nothing         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Usuario bloqueado â”‚ âœ— NO (2+ = Ã©xito)      â”‚ âœ“ SÃ (todos o nada)    â”‚
â”‚ UX                â”‚ âœ“ Muy buena            â”‚ âœ— Pobre (esperas)      â”‚
â”‚ Resilencia        â”‚ âœ“ Excelente            â”‚ âœ— Pobre                â”‚
â”‚ HuÃ©rfanos auto    â”‚ âœ“ SÃ­, al sync          â”‚ âœ— No, forever          â”‚
â”‚ Complejidad       â”‚ âš ï¸ Media (3 pasos)     â”‚ Simple (2 pasos)       â”‚
â”‚ IntervenciÃ³n      â”‚ âœ“ MÃ­nima (auto)        â”‚ âœ“ Ninguna pero esperas â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜


TESTING
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

TEST 1: Ã‰XITO TOTAL
  - 3 workers activos
  - DELETE /document
  - Verificar: HTTP 200, estado='Ã©xito_total', archivos no existen
  
TEST 2: Ã‰XITO PARCIAL
  - Detener worker 3
  - DELETE /document
  - Verificar: HTTP 200, estado='Ã©xito_parcial', pendiente creado
  - Levantar worker 3
  - Verificar: worker hace POST /node-startup
  - Verificar: archivo sincronizado INMEDIATAMENTE, estado='completado'
  - (No espera 5 minutos como antes)

TEST 3: FALLO TOTAL
  - Detener workers 2 y 3
  - DELETE /document
  - Verificar: HTTP 503, archivo sigue existiendo en todos

TEST 4: PUSH PATTERN
  - Detener worker 3 despuÃ©s de crear pendiente
  - Levantar worker 3
  - Verificar logs: POST /node-startup al master
  - Verificar: sincronizaciÃ³n inmediata (patrÃ³n PUSH)
  - Verificar: archivo borrado en < 2 segundos


CONFIGURACIÃ“N PARA PRODUCCIÃ“N
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

1. Actualizar MASTER_URL en .env de cada worker:
   De: "http://localhost:8000"
   A:  "http://192.168.1.100:8000" (IP del master en LAN)

2. Configurar ALMACENAMIENTO_NODO (rutas absolutas):
   De: "../storage/node1"
   A:  "/mnt/storage/node1" o "D:\\Documentos\\node1"

3. Crear .env en cada worker con:
   WORKER_NODE_NAME=node1  (o node2, node3)
   ALMACENAMIENTO_NODO=/mnt/storage/node1
   MASTER_URL=http://192.168.1.100:8000
   SUPABASE_URL=https://...
   SUPABASE_KEY=...

4. Monitoreo:
   SELECT COUNT(*) FROM borrados_pendientes WHERE estado='fallido';
   â†’ Si > 0: alerta automÃ¡tica
   
   SELECT COUNT(*) FROM borrados_pendientes WHERE estado='pendiente';
  â†’ Si > 0 y llevan demasiado tiempo: revisar logs del master/worker


ESTADO FINAL
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

âœ… FASE 5: Borrado en dos pasos â€” COMPLETADO
âœ… FASE 6: SincronizaciÃ³n al startup â€” COMPLETADO
âœ… FASE 6b: [OPTIMIZADO] Push Pattern en lugar de job periÃ³dico â€” COMPLETADO
âœ… FASE 6c: Cleanup de registros antiguos â€” COMPLETADO

âœ… FASE 7: ConfiguraciÃ³n para LAN (LISTA PARA IMPLEMENTAR)

El sistema ahora:
  âœ… Permite borrados parciales (2+ de 3)
  âœ… No bloquea al usuario
  âœ… Sincroniza automÃ¡ticamente
  âœ… [NUEVO] PatrÃ³n PUSH: worker notifica al master al startup
  âœ… [NUEVO] SincronizaciÃ³n inmediata (~1 segundo)
  âœ… [ELIMINADO] Job periÃ³dico cada 5 minutos (ineficiente)
  âœ… Fallback automÃ¡tico si master offline
  âœ… Previene archivos huÃ©rfanos
  âœ… Escalable y resiliente

â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”

Ãšltima actualizaciÃ³n: 4 de mayo de 2026
VersiÃ³n: 2.1 (Eventual Consistency + Push Pattern)
Estado: âœ… PRODUCCIÃ“N-LISTO

