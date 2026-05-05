# Recomendaciones PrÃ¡cticas â€” Schema Supabase

## ðŸŽ¯ RESUMEN EJECUTIVO

Tu schema nuevo es **infinitamente mejor** que el stub. AquÃ­ hay lo que necesitas hacer:

---

## âœ… FASE 1: ImplementaciÃ³n Base (CRÃTICA)

### 1ï¸âƒ£ Ejecutar el SQL completo en Supabase

Copia todo el SQL del nuevo schema en:
`Supabase â†’ Tu Proyecto â†’ SQL Editor â†’ Pega TODO y Ejecuta`

El schema incluye:
- âœ… 9 tablas normalizadas
- âœ… Ãndices optimizados
- âœ… 1 trigger automÃ¡tico (crear "General" al registrar usuario)
- âœ… 3 vistas para queries complejas

### 2ï¸âƒ£ Agregar 4 Tablas CrÃ­ticas

Copia el SQL de `SCHEMA_SUPABASE_OPTIMIZADO.md`:

**A. `auditoria_documentos`** (QuiÃ©n clasificÃ³, cuÃ¡ndo, resultado)
```
Prioridad: ðŸ”´ ALTA
Usa para: Debugging de clasificaciones errÃ³neas
```

**B. `logs_errores_clasificacion`** (Rastrear timeouts, fallos)
```
Prioridad: ðŸŸ¡ MEDIA
Usa para: Monitoreo de workers
```

**C. `cuotas_usuario`** (LÃ­mites de almacenamiento)
```
Prioridad: ðŸŸ¡ MEDIA
Usa para: Cobro futuro / lÃ­mites SaaS
```

**D. `sincronizacion_nodos`** (Verificar integridad de replicaciÃ³n)
```
Prioridad: ðŸŸ¢ BAJA (despuÃ©s)
Usa para: Validar que los 3 nodos tienen copias idÃ©nticas
```

### 3ï¸âƒ£ Mejorar 3 Tablas Existentes

**Tabla `documentos`:**
- Agregar: `hash_original`, `paginas`, `estado`, `confianza_clasificacion`
- Quitar: Nada (backward compatible)

**Tabla `consenso_votos`:**
- Renombrar: `nodo` â†’ `nodo_worker` (claridad)
- Agregar: `confianza_worker` (para debugging)

**Tabla `lider_actual`:**
- Agregar: `heartbeat_interval` (configurable)
- Agregar: trigger `trg_actualizar_heartbeat`

---

## ðŸ“‹ FASE 2: IntegraciÃ³n con Code (1-2 dÃ­as)

### Actualizar `master/database.py`

âœ… **YA HECHO** - El archivo ya tiene 60+ funciones:

```python
# Usuarios
obtener_usuario_por_nombre()
insertar_usuario()
actualizar_usuario()

# Tokens
crear_token_sesion()
obtener_token()
revocar_token()

# TemÃ¡ticas
obtener_tematicas_usuario()
insertar_tematica()

# Documentos
insertar_documento()
obtener_documentos_usuario()
actualizar_documento_clasificacion()

# Consenso
insertar_voto_consenso()
obtener_votos_documento()

# Nodos
insertar_nodo_replicacion()
obtener_nodos_documento()

# AuditorÃ­a
registrar_auditoria()

# Liderazgo
actualizar_lider()
obtener_lider()
heartbeat_lider()
```

### Actualizar `master/routes.py`


El flujo actual debe leer y escribir directamente en Supabase:

```python
from master.database import obtener_usuario_por_nombre

usuario = obtener_usuario_por_nombre(username)
```

### Actualizar `master/consensus.py`

Cuando registres los votos, usar:

```python
from master.database import (
    insertar_voto_consenso,
    obtener_votos_documento,
    registrar_auditoria
)

# DespuÃ©s de clasificar
for nodo_worker, resultado in resultados.items():
    insertar_voto_consenso(
        documento_id,
        nodo_worker,
        resultado['area_predicha'],
        resultado['confianza']
    )

# Registrar auditorÃ­a
registrar_auditoria(
    documento_id,
    usuario_id,
    accion='clasificacion',
    area_nueva=area_final,
    confianza=confianza_consenso
)
```

---

## ðŸ”§ FASE 3: ValidaciÃ³n (2-3 dÃ­as)

### 1. Pruebas unitarias para database.py

```python
# test_database.py
def test_crear_usuario():
    usuario_id = insertar_usuario("test_user", "hash123")
    assert usuario_id is not None
    
    usuario = obtener_usuario_por_id(usuario_id)
    assert usuario['username'] == "test_user"

def test_token_sesion():
    token_id = crear_token_sesion(usuario_id, "hash_token", "2026-04-23T12:00:00Z")
    token = obtener_token("hash_token")
    assert token['usuario_id'] == usuario_id
```

### 2. Pruebas de flujo end-to-end

```
1. Registrar usuario â†’ Crear temÃ¡tica â†’ Crear subtemÃ¡tica
2. Subir PDF â†’ Registrar documento â†’ Consenso â†’ Guardar votos
3. Verificar auditorÃ­a â†’ Verificar nodos replicados
4. Eliminar documento â†’ Verificar soft delete
```

---

## ðŸ“Š MAPPING: CÃ³digo Existente â†’ Supabase

| Archivo | Cambio | FunciÃ³n |
|---------|--------|---------|
| **auth.py** | Hash contraseÃ±a + generar token | `insertar_usuario()`, `crear_token_sesion()` |
| **routes.py** | POST /upload â†’ registrar documento | `insertar_documento()`, `insertar_voto_consenso()` |
| **consensus.py** | Calcular mayorÃ­a + guardar votos | `insertar_voto_consenso()`, `registrar_auditoria()` |
| **adapter.py** | Mapear Ã¡rea â†’ subtemÃ¡tica | `actualizar_documento_clasificacion()` |
| **election.py** | Actualizar lÃ­der | `actualizar_lider()`, `heartbeat_lider()` |
| **deletion_coordinator.py** | Borrado en 2 pasos | `marcar_documento_eliminado()` |

---

## ðŸš€ CHECKLIST: Antes de ProducciÃ³n

- [ ] SQL ejecutado en Supabase
- [ ] 4 tablas adicionales creadas
- [ ] 3 tablas mejoradas
- [ ] database.py con todas las funciones
- [ ] routes.py integrado con database.py
- [ ] consensus.py registra votos
- [ ] Tests unitarios pasan
- [ ] Tests e2e pasan
- [ ] Variables de entorno configuradas (SUPABASE_URL, SUPABASE_KEY)
- [ ] Logs de auditorÃ­a generÃ¡ndose
- [ ] Heartbeat del lÃ­der funcionando

---

## ðŸ’¾ Env Variables Requeridas

Crear `.env` en la raÃ­z del proyecto:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_LOG_LEVEL=INFO  # DEBUG para desarrollo
```

---

## ðŸŽ“ Nota TÃ©cnica

El schema nuevo soporta:
- âœ… AuditorÃ­a completa de cambios
- âœ… ReplicaciÃ³n distribuida verificada
- âœ… Tolerancia a fallos de workers (2/3 mayorÃ­a)
- âœ… Tracking de liderazgo (HA)
- âœ… Soft deletes (preservar historial)
- âœ… Cuotas de usuario (preparado para billing)

Es production-ready. Solo necesitas integrar las funciones en los endpoints.

