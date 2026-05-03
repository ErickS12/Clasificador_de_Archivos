# 📊 COMPARACIÓN: Esquema ANTES vs DESPUÉS

## Vista Rápida: Cambios principales en SQL

---

## 1. Tabla `tematicas`

### ❌ ANTES (en tu Supabase)
```sql
CREATE TABLE tematicas (
    id           INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    usuario_id   UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre       TEXT NOT NULL,
    es_general   BOOLEAN DEFAULT FALSE,
    creado_en    TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_tematica_usuario UNIQUE (usuario_id, nombre),
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- Cada usuario tenía sus propias categorías
-- juan@mail.com podría tener "IA"
-- maria@mail.com podría tener "Inteligencia Artificial"
-- (mismo concepto, nombres diferentes)
```

### ✅ DESPUÉS (en el código local)
```sql
CREATE TABLE tematicas (
    id           INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    -- usuario_id   ← REMOVIDO ❌
    nombre       TEXT NOT NULL,
    es_general   BOOLEAN DEFAULT FALSE,
    creado_en    TIMESTAMPTZ DEFAULT now(),

    -- CONSTRAINT uq_tematica_usuario ← REMOVIDO ❌
    CONSTRAINT uq_tematica_nombre UNIQUE (nombre),  -- ← AGREGADO ✅
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- Catálogo global - IGUAL para todos los usuarios
INSERT INTO tematicas (nombre, es_general) VALUES
    ('Tecnología', FALSE),
    ('Ciencias', FALSE),
    ('Otros', TRUE);
```

**Impacto:**
- ✅ Todas las categorías son globales
- ✅ Usuarios no pueden duplicar nombres
- ✅ Menor complejidad en queries
- ✅ ML tiene datos consistentes

---

## 2. Tabla `subtematicas`

### ❌ ANTES
```sql
CREATE TABLE subtematicas (
    id            INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tematica_id   INT NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    nombre        TEXT NOT NULL,
    creado_en     TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_subtematica_tema UNIQUE (tematica_id, nombre),
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- Vacía o con datos sueltos creados por usuarios
-- Cada usuario crearía sus propias subcategorías
```

### ✅ DESPUÉS
```sql
CREATE TABLE subtematicas (
    id            INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tematica_id   INT NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    nombre        TEXT NOT NULL,
    creado_en     TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_subtematica_tema UNIQUE (tematica_id, nombre),
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- Ahora poblada con catálogo FIJO de 8 subcategorías
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Inteligencia Artificial' FROM tematicas WHERE nombre = 'Tecnología';
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Redes' FROM tematicas WHERE nombre = 'Tecnología';
-- ... (6 inserts más)
```

**Estructura final:**
```
Tecnología (ID: 1)
├─ Inteligencia Artificial (ID: 1)
├─ Redes (ID: 2)
├─ Bases de Datos (ID: 3)
├─ Sistemas Operativos (ID: 4)
└─ Sistemas Distribuidos (ID: 5)

Ciencias (ID: 2)
├─ Biología (ID: 6)
└─ Matemáticas (ID: 7)

Otros (ID: 3)
└─ General (ID: 8)
```

---

## 3. Triggers: `trg_crear_general`

### ❌ ANTES (en tu Supabase)
```sql
-- Automáticamente creaba una categoría "General" para cada usuario nuevo
CREATE OR REPLACE FUNCTION crear_tematica_general()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO tematicas (usuario_id, nombre, es_general)
    VALUES (NEW.id, 'General', TRUE);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_crear_general
AFTER INSERT ON usuarios
FOR EACH ROW
EXECUTE FUNCTION crear_tematica_general();

-- Problema: Cada usuario tenía su "General" → inconsistencia
```

### ✅ DESPUÉS
```sql
-- TRIGGER REMOVIDO ❌
DROP TRIGGER IF EXISTS trg_crear_general ON usuarios;
DROP FUNCTION IF EXISTS crear_tematica_general();

-- Hay un solo "General" en Otros/General
-- Todos los usuarios lo comparten
```

---

## 4. Tabla `documentos` (sin cambios principales)

```sql
-- Sigue igual, pero ahora:
CREATE TABLE documentos (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id              UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    
    -- Sigue apuntando a tematica global (no por usuario)
    tematica_id             INT NOT NULL REFERENCES tematicas(id),
    subtematica_id          INT REFERENCES subtematicas(id),
    
    -- ... resto de columnas igual
);

-- Cambio de lógica:
-- ANTES: documento.tematica_id → en tabla tematicas donde usuario_id = ?
-- AHORA: documento.tematica_id → en tabla tematicas global
--        documento.usuario_id → privacidad (solo ve sus docs)
```

---

## 5. Vista `vista_arbol_usuario`

### ❌ ANTES
```sql
CREATE OR REPLACE VIEW vista_arbol_usuario AS
SELECT
    u.username,
    t.id, t.nombre, t.es_general,
    s.id, s.nombre,
    COUNT(d.id) AS total_documentos
FROM usuarios u
JOIN tematicas t ON t.usuario_id = u.id  -- ← JOIN por usuario
LEFT JOIN subtematicas s ON s.tematica_id = t.id
LEFT JOIN documentos d ON d.tematica_id = t.id
    AND (d.subtematica_id = s.id OR ...)
    AND d.estado = 'activo'
    AND d.usuario_id = u.id
GROUP BY ...;

-- Resultado: Cada usuario ve solo SUS categorías personales
-- ┌─────────┬─────────────────────┐
-- │ usuario │ tematica            │
-- ├─────────┼─────────────────────┤
-- │ juan    │ Mi IA               │
-- │ juan    │ Mis Redes           │
-- │ maria   │ IA de Maria         │
-- │ maria   │ Ciencias de Maria   │
-- └─────────┴─────────────────────┘
```

### ✅ DESPUÉS
```sql
CREATE OR REPLACE VIEW vista_arbol_usuario AS
SELECT
    u.username,
    t.id, t.nombre, t.es_general,
    s.id, s.nombre,
    COUNT(d.id) AS total_documentos
FROM usuarios u
CROSS JOIN tematicas t  -- ← CROSS JOIN (todas las categorías globales)
LEFT JOIN subtematicas s ON s.tematica_id = t.id
LEFT JOIN documentos d ON d.usuario_id = u.id  -- ← Filtrar por usuario
    AND d.tematica_id = t.id
    AND (d.subtematica_id = s.id OR ...)
    AND d.estado = 'activo'
GROUP BY ...;

-- Resultado: Cada usuario ve EL MISMO catálogo
-- ┌─────────┬──────────────────────────────┐
-- │ usuario │ tematica/subtematica         │
-- ├─────────┼──────────────────────────────┤
-- │ juan    │ Tecnología / Inteligencia AI │
-- │ juan    │ Tecnología / Redes           │
-- │ juan    │ Tecnología / Bases de Datos  │
-- │ maria   │ Tecnología / Inteligencia AI │ ← MISMO CATÁLOGO
-- │ maria   │ Tecnología / Redes           │
-- │ maria   │ Ciencias / Biología          │
-- └─────────┴──────────────────────────────┘

-- Pero COUNT de documentos es POR USUARIO
-- ┌─────────┬────────────────────────────────┬──────────────────┐
-- │ usuario │ tematica/subtematica           │ total_documentos │
-- ├─────────┼────────────────────────────────┼──────────────────┤
-- │ juan    │ Tecnología / Redes             │ 2                │
-- │ maria   │ Tecnología / Redes             │ 5                │
-- └─────────┴────────────────────────────────┴──────────────────┘
```

---

## 6. Tabla `lider_actual` (sin cambios)

```sql
-- Sigue exactamente igual, no afectada
```

---

## 7. Tabla `consenso_votos` (sin cambios principales)

```sql
-- Antes: Guardaba votos sobre categorías per-usuario
-- Ahora: Guarda votos sobre categorías globales

-- Estructura igual, pero:
-- ANTES: voto = usuario_area_name: "Mi IA"
-- AHORA: voto = ruta_global: "Tecnología/Inteligencia Artificial"
```

---

## 📋 RESUMEN DE CAMBIOS POR TABLA

| Tabla | Cambios |
|-------|---------|
| `usuarios` | ✅ Sin cambios |
| `tematicas` | ❌ Removido `usuario_id`, ✅ Agregado `UNIQUE(nombre)`, ✅ Insertados 3 registros |
| `subtematicas` | ✅ Sin cambios estructurales, ✅ Insertados 8 registros |
| `documentos` | ✅ Sin cambios estructurales |
| `nodos_almacenamiento` | ✅ Sin cambios |
| `consenso_votos` | ✅ Sin cambios estructurales |
| `lider_actual` | ✅ Sin cambios |
| `vista_arbol_usuario` | ⚠️ Lógica cambiada (CROSS JOIN) |

---

## 🔄 MIGRACIÓN PASO A PASO

```
Estado ANTES (Supabase actual):
┌──────────────────────────────────────────┐
│ tematicas (con usuario_id, datos viejos) │
│ - Juan's IA                              │
│ - Juan's Redes                           │
│ - Maria's IA (diferente)                 │
│ - Maria's Ciencias                       │
└──────────────────────────────────────────┘
         ↓
    [Ejecutar migración]
         ↓
Estado DESPUÉS:
┌──────────────────────────────────────────┐
│ tematicas (SIN usuario_id, globales)     │
│ - Tecnología                             │
│ - Ciencias                               │
│ - Otros                                  │
└──────────────────────────────────────────┘
┌──────────────────────────────────────────┐
│ subtematicas (8 subcategorías fijas)     │
│ - Inteligencia Artificial                │
│ - Redes                                  │
│ - Biología                               │
│ - etc...                                 │
└──────────────────────────────────────────┘
```

---

## 🎯 VERIFICACIÓN DESPUÉS DE MIGRAR

```sql
-- 1. Verificar que usuario_id fue removido
SELECT column_name FROM information_schema.columns
WHERE table_name = 'tematicas';
-- NO debe mostrar usuario_id ✅

-- 2. Verificar que hay 3 tematicas globales
SELECT * FROM tematicas;
-- Resultado esperado:
-- id │ nombre      │ es_general
-- ───┼─────────────┼───────────
--  1 │ Tecnología  │ false
--  2 │ Ciencias    │ false
--  3 │ Otros       │ true

-- 3. Verificar que hay 8 subtematicas
SELECT t.nombre, s.nombre FROM subtematicas s
JOIN tematicas t ON t.id = s.tematica_id;
-- Resultado esperado: 8 registros

-- 4. Verificar vista funciona
SELECT DISTINCT username, tematica FROM vista_arbol_usuario;
-- Resultado esperado: Mismo catálogo para todos
```

---

## ⚠️ PUNTOS CRÍTICOS DURANTE MIGRACIÓN

```
🔴 CRÍTICO 1: DELETE de tematicas viejas
   → Elimina datos per-usuario
   → Pero no toca documentos (CASCADE no aplica aquí)
   → Los documentos quedan "huérfanos" si su FK apunta a
     una tematica que se borra

🔴 CRÍTICO 2: Remover usuario_id
   → Las vistas viejas se rompen
   → Se han actualizado en el archivo

🔴 CRÍTICO 3: Orden de operaciones
   → PRIMERO: Remover constraints
   → LUEGO: Borrar datos viejos
   → LUEGO: Remover columna
   → FINALMENTE: Insertar datos nuevos

✅ SOLUCIÓN: El script MIGRACION_CATALOGO_GLOBAL.sql
   lo hace todo en orden correcto
```

---

**¿Necesitas más detalles?** Ver:
- `MIGRACION_CATALOGO_GLOBAL.sql` - Script completo
- `GUIA_APLICAR_CAMBIOS_SUPABASE.md` - Instrucciones paso a paso
