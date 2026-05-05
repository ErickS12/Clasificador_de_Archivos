# ðŸ“Š COMPARACIÃ“N: Esquema ANTES vs DESPUÃ‰S

## Vista RÃ¡pida: Cambios principales en SQL

---

## 1. Tabla `tematicas`

### âŒ ANTES (en tu Supabase)
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

-- Cada usuario tenÃ­a sus propias categorÃ­as
-- juan@mail.com podrÃ­a tener "IA"
-- maria@mail.com podrÃ­a tener "Inteligencia Artificial"
-- (mismo concepto, nombres diferentes)
```

### âœ… DESPUÃ‰S (en el cÃ³digo local)
```sql
CREATE TABLE tematicas (
    id           INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    -- usuario_id   â† REMOVIDO âŒ
    nombre       TEXT NOT NULL,
    es_general   BOOLEAN DEFAULT FALSE,
    creado_en    TIMESTAMPTZ DEFAULT now(),

    -- CONSTRAINT uq_tematica_usuario â† REMOVIDO âŒ
    CONSTRAINT uq_tematica_nombre UNIQUE (nombre),  -- â† AGREGADO âœ…
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- CatÃ¡logo global - IGUAL para todos los usuarios
INSERT INTO tematicas (nombre, es_general) VALUES
    ('TecnologÃ­a', FALSE),
    ('Ciencias', FALSE),
    ('Otros', TRUE);
```

**Impacto:**
- âœ… Todas las categorÃ­as son globales
- âœ… Usuarios no pueden duplicar nombres
- âœ… Menor complejidad en queries
- âœ… ML tiene datos consistentes

---

## 2. Tabla `subtematicas`

### âŒ ANTES
```sql
CREATE TABLE subtematicas (
    id            INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tematica_id   INT NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    nombre        TEXT NOT NULL,
    creado_en     TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_subtematica_tema UNIQUE (tematica_id, nombre),
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- VacÃ­a o con datos sueltos creados por usuarios
-- Cada usuario crearÃ­a sus propias subcategorÃ­as
```

### âœ… DESPUÃ‰S
```sql
CREATE TABLE subtematicas (
    id            INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tematica_id   INT NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    nombre        TEXT NOT NULL,
    creado_en     TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_subtematica_tema UNIQUE (tematica_id, nombre),
    CONSTRAINT ck_nombre_no_vacio CHECK (trim(nombre) != '')
);

-- Ahora poblada con catÃ¡logo FIJO de 8 subcategorÃ­as
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Inteligencia Artificial' FROM tematicas WHERE nombre = 'TecnologÃ­a';
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Redes' FROM tematicas WHERE nombre = 'TecnologÃ­a';
-- ... (6 inserts mÃ¡s)
```

**Estructura final:**
```
TecnologÃ­a (ID: 1)
â”œâ”€ Inteligencia Artificial (ID: 1)
â”œâ”€ Redes (ID: 2)
â”œâ”€ Bases de Datos (ID: 3)
â”œâ”€ Sistemas Operativos (ID: 4)
â””â”€ Sistemas Distribuidos (ID: 5)

Ciencias (ID: 2)
â”œâ”€ BiologÃ­a (ID: 6)
â””â”€ MatemÃ¡ticas (ID: 7)

Otros (ID: 3)
â””â”€ General (ID: 8)
```

---

## 3. Triggers: `trg_crear_general`

### âŒ ANTES (en tu Supabase)
```sql
-- AutomÃ¡ticamente creaba una categorÃ­a "General" para cada usuario nuevo
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

-- Problema: Cada usuario tenÃ­a su "General" â†’ inconsistencia
```

### âœ… DESPUÃ‰S
```sql
-- TRIGGER REMOVIDO âŒ
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

-- Cambio de lÃ³gica:
-- ANTES: documento.tematica_id â†’ en tabla tematicas donde usuario_id = ?
-- AHORA: documento.tematica_id â†’ en tabla tematicas global
--        documento.usuario_id â†’ privacidad (solo ve sus docs)
```

---

## 5. Vista `vista_arbol_usuario`

### âŒ ANTES
```sql
CREATE OR REPLACE VIEW vista_arbol_usuario AS
SELECT
    u.username,
    t.id, t.nombre, t.es_general,
    s.id, s.nombre,
    COUNT(d.id) AS total_documentos
FROM usuarios u
JOIN tematicas t ON t.usuario_id = u.id  -- â† JOIN por usuario
LEFT JOIN subtematicas s ON s.tematica_id = t.id
LEFT JOIN documentos d ON d.tematica_id = t.id
    AND (d.subtematica_id = s.id OR ...)
    AND d.estado = 'activo'
    AND d.usuario_id = u.id
GROUP BY ...;

-- Resultado: Cada usuario ve solo SUS categorÃ­as personales
-- â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
-- â”‚ usuario â”‚ tematica            â”‚
-- â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
-- â”‚ juan    â”‚ Mi IA               â”‚
-- â”‚ juan    â”‚ Mis Redes           â”‚
-- â”‚ maria   â”‚ IA de Maria         â”‚
-- â”‚ maria   â”‚ Ciencias de Maria   â”‚
-- â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### âœ… DESPUÃ‰S
```sql
CREATE OR REPLACE VIEW vista_arbol_usuario AS
SELECT
    u.username,
    t.id, t.nombre, t.es_general,
    s.id, s.nombre,
    COUNT(d.id) AS total_documentos
FROM usuarios u
CROSS JOIN tematicas t  -- â† CROSS JOIN (todas las categorÃ­as globales)
LEFT JOIN subtematicas s ON s.tematica_id = t.id
LEFT JOIN documentos d ON d.usuario_id = u.id  -- â† Filtrar por usuario
    AND d.tematica_id = t.id
    AND (d.subtematica_id = s.id OR ...)
    AND d.estado = 'activo'
GROUP BY ...;

-- Resultado: Cada usuario ve EL MISMO catÃ¡logo
-- â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
-- â”‚ usuario â”‚ tematica/subtematica         â”‚
-- â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
-- â”‚ juan    â”‚ TecnologÃ­a / Inteligencia AI â”‚
-- â”‚ juan    â”‚ TecnologÃ­a / Redes           â”‚
-- â”‚ juan    â”‚ TecnologÃ­a / Bases de Datos  â”‚
-- â”‚ maria   â”‚ TecnologÃ­a / Inteligencia AI â”‚ â† MISMO CATÃLOGO
-- â”‚ maria   â”‚ TecnologÃ­a / Redes           â”‚
-- â”‚ maria   â”‚ Ciencias / BiologÃ­a          â”‚
-- â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

-- Pero COUNT de documentos es POR USUARIO
-- â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
-- â”‚ usuario â”‚ tematica/subtematica           â”‚ total_documentos â”‚
-- â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
-- â”‚ juan    â”‚ TecnologÃ­a / Redes             â”‚ 2                â”‚
-- â”‚ maria   â”‚ TecnologÃ­a / Redes             â”‚ 5                â”‚
-- â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 6. Tabla `lider_actual` (sin cambios)

```sql
-- Sigue exactamente igual, no afectada
```

---

## 7. Tabla `consenso_votos` (sin cambios principales)

```sql
-- Antes: Guardaba votos sobre categorÃ­as per-usuario
-- Ahora: Guarda votos sobre categorÃ­as globales

-- Estructura igual, pero:
-- ANTES: voto = usuario_area_name: "Mi IA"
-- AHORA: voto = ruta_global: "TecnologÃ­a/Inteligencia Artificial"
```

---

## ðŸ“‹ RESUMEN DE CAMBIOS POR TABLA

| Tabla | Cambios |
|-------|---------|
| `usuarios` | âœ… Sin cambios |
| `tematicas` | âŒ Removido `usuario_id`, âœ… Agregado `UNIQUE(nombre)`, âœ… Insertados 3 registros |
| `subtematicas` | âœ… Sin cambios estructurales, âœ… Insertados 8 registros |
| `documentos` | âœ… Sin cambios estructurales |
| `nodos_almacenamiento` | âœ… Sin cambios |
| `consenso_votos` | âœ… Sin cambios estructurales |
| `lider_actual` | âœ… Sin cambios |
| `vista_arbol_usuario` | âš ï¸ LÃ³gica cambiada (CROSS JOIN) |

---

## ðŸ”„ MIGRACIÃ“N PASO A PASO

```
Estado ANTES (Supabase actual):
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ tematicas (con usuario_id, datos viejos) â”‚
â”‚ - Juan's IA                              â”‚
â”‚ - Juan's Redes                           â”‚
â”‚ - Maria's IA (diferente)                 â”‚
â”‚ - Maria's Ciencias                       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â†“
    [Ejecutar migraciÃ³n]
         â†“
Estado DESPUÃ‰S:
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ tematicas (SIN usuario_id, globales)     â”‚
â”‚ - TecnologÃ­a                             â”‚
â”‚ - Ciencias                               â”‚
â”‚ - Otros                                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ subtematicas (8 subcategorÃ­as fijas)     â”‚
â”‚ - Inteligencia Artificial                â”‚
â”‚ - Redes                                  â”‚
â”‚ - BiologÃ­a                               â”‚
â”‚ - etc...                                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## ðŸŽ¯ VERIFICACIÃ“N DESPUÃ‰S DE MIGRAR

```sql
-- 1. Verificar que usuario_id fue removido
SELECT column_name FROM information_schema.columns
WHERE table_name = 'tematicas';
-- NO debe mostrar usuario_id âœ…

-- 2. Verificar que hay 3 tematicas globales
SELECT * FROM tematicas;
-- Resultado esperado:
-- id â”‚ nombre      â”‚ es_general
-- â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
--  1 â”‚ TecnologÃ­a  â”‚ false
--  2 â”‚ Ciencias    â”‚ false
--  3 â”‚ Otros       â”‚ true

-- 3. Verificar que hay 8 subtematicas
SELECT t.nombre, s.nombre FROM subtematicas s
JOIN tematicas t ON t.id = s.tematica_id;
-- Resultado esperado: 8 registros

-- 4. Verificar vista funciona
SELECT DISTINCT username, tematica FROM vista_arbol_usuario;
-- Resultado esperado: Mismo catÃ¡logo para todos
```

---

## âš ï¸ PUNTOS CRÃTICOS DURANTE MIGRACIÃ“N

```
ðŸ”´ CRÃTICO 1: DELETE de tematicas viejas
   â†’ Elimina datos per-usuario
   â†’ Pero no toca documentos (CASCADE no aplica aquÃ­)
   â†’ Los documentos quedan "huÃ©rfanos" si su FK apunta a
     una tematica que se borra

ðŸ”´ CRÃTICO 2: Remover usuario_id
   â†’ Las vistas viejas se rompen
   â†’ Se han actualizado en el archivo

ðŸ”´ CRÃTICO 3: Orden de operaciones
   â†’ PRIMERO: Remover constraints
   â†’ LUEGO: Borrar datos viejos
   â†’ LUEGO: Remover columna
   â†’ FINALMENTE: Insertar datos nuevos

âœ… SOLUCIÃ“N: El script MIGRACION_CATALOGO_GLOBAL.sql
   lo hace todo en orden correcto
```

---

**Â¿Necesitas mÃ¡s detalles?** Ver:
- `MIGRACION_CATALOGO_GLOBAL.sql` - Script completo
- `GUIA_APLICAR_CAMBIOS_SUPABASE.md` - Instrucciones paso a paso

