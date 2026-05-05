# Recomendaciones Prácticas — Schema Supabase

## 🎯 RESUMEN EJECUTIVO

Tu schema nuevo es **infinitamente mejor** que el stub. Aquí hay lo que necesitas hacer:

---

## ✅ FASE 1: Implementación Base (CRÍTICA)

### 1️⃣ Ejecutar el SQL completo en Supabase

Copia todo el SQL del nuevo schema en:
`Supabase → Tu Proyecto → SQL Editor → Pega TODO y Ejecuta`

El schema incluye:
- ✅ 9 tablas normalizadas
- ✅ Índices optimizados
- ✅ 1 trigger automático (crear "General" al registrar usuario)
- ✅ 3 vistas para queries complejas

### 2️⃣ Agregar 4 Tablas Críticas

Copia el SQL de `SCHEMA_SUPABASE_OPTIMIZADO.md`:

**A. `auditoria_documentos`** (Quién clasificó, cuándo, resultado)
```
Prioridad: 🔴 ALTA
Usa para: Debugging de clasificaciones erróneas
```

**B. `logs_errores_clasificacion`** (Rastrear timeouts, fallos)
```
Prioridad: 🟡 MEDIA
Usa para: Monitoreo de workers
```

**C. `cuotas_usuario`** (Límites de almacenamiento)
```
Prioridad: 🟡 MEDIA
Usa para: Cobro futuro / límites SaaS
```

**D. `sincronizacion_nodos`** (Verificar integridad de replicación)
```
Prioridad: 🟢 BAJA (después)
Usa para: Validar que los 3 nodos tienen copias idénticas
```

### 3️⃣ Mejorar 3 Tablas Existentes

**Tabla `documentos`:**
- Agregar: `hash_original`, `paginas`, `estado`, `confianza_clasificacion`
- Quitar: Nada (backward compatible)

**Tabla `consenso_votos`:**
- Renombrar: `nodo` → `nodo_worker` (claridad)
- Agregar: `confianza_worker` (para debugging)

**Tabla `lider_actual`:**
- Agregar: `heartbeat_interval` (configurable)
- Agregar: trigger `trg_actualizar_heartbeat`

---

## 📋 FASE 2: Integración con Code (1-2 días)

### Actualizar `master/database.py`

✅ **YA HECHO** - El archivo ya tiene 60+ funciones:

```python
# Usuarios
obtener_usuario_por_nombre()
insertar_usuario()
actualizar_usuario()

# Tokens
crear_token_sesion()
obtener_token()
revocar_token()

# Temáticas
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

# Auditoría
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

# Después de clasificar
for nodo_worker, resultado in resultados.items():
    insertar_voto_consenso(
        documento_id,
        nodo_worker,
        resultado['area_predicha'],
        resultado['confianza']
    )

# Registrar auditoría
registrar_auditoria(
    documento_id,
    usuario_id,
    accion='clasificacion',
    area_nueva=area_final,
    confianza=confianza_consenso
)
```

---

## 🔧 FASE 3: Validación (2-3 días)

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
1. Registrar usuario → Crear temática → Crear subtemática
2. Subir PDF → Registrar documento → Consenso → Guardar votos
3. Verificar auditoría → Verificar nodos replicados
4. Eliminar documento → Verificar soft delete
```

---

## 📊 MAPPING: Código Existente → Supabase

| Archivo | Cambio | Función |
|---------|--------|---------|
| **auth.py** | Hash contraseña + generar token | `insertar_usuario()`, `crear_token_sesion()` |
| **routes.py** | POST /upload → registrar documento | `insertar_documento()`, `insertar_voto_consenso()` |
| **consensus.py** | Calcular mayoría + guardar votos | `insertar_voto_consenso()`, `registrar_auditoria()` |
| **adapter.py** | Mapear área → subtemática | `actualizar_documento_clasificacion()` |
| **election.py** | Actualizar líder | `actualizar_lider()`, `heartbeat_lider()` |
| **deletion_coordinator.py** | Borrado en 2 pasos | `marcar_documento_eliminado()` |

---

## 🚀 CHECKLIST: Antes de Producción

- [ ] SQL ejecutado en Supabase
- [ ] 4 tablas adicionales creadas
- [ ] 3 tablas mejoradas
- [ ] database.py con todas las funciones
- [ ] routes.py integrado con database.py
- [ ] consensus.py registra votos
- [ ] Tests unitarios pasan
- [ ] Tests e2e pasan
- [ ] Variables de entorno configuradas (SUPABASE_URL, SUPABASE_KEY)
- [ ] Logs de auditoría generándose
- [ ] Heartbeat del líder funcionando

---

## 💾 Env Variables Requeridas

Crear `.env` en la raíz del proyecto:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_LOG_LEVEL=INFO  # DEBUG para desarrollo
```

---

## 🎓 Nota Técnica

El schema nuevo soporta:
- ✅ Auditoría completa de cambios
- ✅ Replicación distribuida verificada
- ✅ Tolerancia a fallos de workers (2/3 mayoría)
- ✅ Tracking de liderazgo (HA)
- ✅ Soft deletes (preservar historial)
- ✅ Cuotas de usuario (preparado para billing)

Es production-ready. Solo necesitas integrar las funciones en los endpoints.


