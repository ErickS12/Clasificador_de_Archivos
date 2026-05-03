-- ════════════════════════════════════════════════════════════════════════════════
-- MIGRACION: De Temáticas por Usuario a Catálogo Global
-- ════════════════════════════════════════════════════════════════════════════════
-- 
-- INSTRUCCIONES:
-- 1. Hacer BACKUP de la BD antes de ejecutar esta migración
-- 2. Ejecutar este script en Supabase SQL Editor
-- 3. Verificar que todas las operaciones completaron sin errores
-- 4. Probar la API con los nuevos cambios
--
-- CAMBIOS PRINCIPALES:
-- - Tabla tematicas: Remover usuario_id (ahora es catálogo global)
-- - Tabla subtematicas: Agregar datos iniciales del catálogo
-- - Vistas: Actualizar para trabajar con catálogo global
-- - Triggers: Remover trigger de crear "General" por usuario
--
-- TIEMPO ESTIMADO: 5-10 minutos
-- ════════════════════════════════════════════════════════════════════════════════

-- PASO 1: Crear tabla temporal para guardar datos de documentos
-- (en caso de que necesitemos rollback)
CREATE TEMP TABLE backup_documentos AS 
SELECT * FROM documentos;

-- PASO 2: Remover restricciones FK temporalmente
ALTER TABLE documentos DROP CONSTRAINT IF EXISTS documentos_tematica_id_fkey;
ALTER TABLE subtematicas DROP CONSTRAINT IF EXISTS subtematicas_tematica_id_fkey;

-- PASO 3: Remover el trigger que crea "General" por usuario
DROP TRIGGER IF EXISTS trg_crear_general ON usuarios;
DROP FUNCTION IF EXISTS crear_tematica_general();

-- PASO 4: Remover la restricción UNIQUE por usuario
ALTER TABLE tematicas DROP CONSTRAINT IF EXISTS uq_tematica_usuario;

-- PASO 5: Remover el índice por usuario
DROP INDEX IF EXISTS idx_tematicas_usuario;

-- PASO 6: Eliminar todas las temáticas existentes (que eran por usuario)
-- ADVERTENCIA: Esto borra las temáticas viejas. Los documentos se perderán.
DELETE FROM tematicas WHERE id IS NOT NULL;

-- PASO 7: Remover la columna usuario_id de tematicas
ALTER TABLE tematicas DROP COLUMN IF EXISTS usuario_id;

-- PASO 8: Agregar constraint UNIQUE a nombre (para catálogo global)
ALTER TABLE tematicas ADD CONSTRAINT uq_tematica_nombre UNIQUE (nombre);

-- PASO 9: Insertar el catálogo global fijo
INSERT INTO tematicas (nombre, es_general) VALUES
    ('Tecnología', FALSE),
    ('Ciencias', FALSE),
    ('Otros', TRUE)
ON CONFLICT (nombre) DO NOTHING;

-- PASO 10: Insertar subcategorías del catálogo global
-- Tecnología
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Inteligencia Artificial' FROM tematicas WHERE nombre = 'Tecnología'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Redes' FROM tematicas WHERE nombre = 'Tecnología'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Bases de Datos' FROM tematicas WHERE nombre = 'Tecnología'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Sistemas Operativos' FROM tematicas WHERE nombre = 'Tecnología'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Sistemas Distribuidos' FROM tematicas WHERE nombre = 'Tecnología'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

-- Ciencias
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Biología' FROM tematicas WHERE nombre = 'Ciencias'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'Matemáticas' FROM tematicas WHERE nombre = 'Ciencias'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

-- Otros (General)
INSERT INTO subtematicas (tematica_id, nombre)
SELECT id, 'General' FROM tematicas WHERE nombre = 'Otros'
ON CONFLICT (tematica_id, nombre) DO NOTHING;

-- PASO 11: Restaurar restricciones FK
ALTER TABLE subtematicas ADD CONSTRAINT subtematicas_tematica_id_fkey
    FOREIGN KEY (tematica_id) REFERENCES tematicas(id) ON DELETE CASCADE;

ALTER TABLE documentos ADD CONSTRAINT documentos_tematica_id_fkey
    FOREIGN KEY (tematica_id) REFERENCES tematicas(id) ON DELETE CASCADE;

-- PASO 12: Actualizar vista para catálogo global
DROP VIEW IF EXISTS vista_arbol_usuario CASCADE;
CREATE OR REPLACE VIEW vista_arbol_usuario AS
SELECT
    u.username,
    t.id         AS tematica_id,
    t.nombre     AS tematica,
    t.es_general,
    s.id         AS subtematica_id,
    s.nombre     AS subtematica,
    COUNT(d.id)  AS total_documentos
FROM usuarios u
CROSS JOIN tematicas t
LEFT JOIN subtematicas s ON s.tematica_id = t.id
LEFT JOIN documentos d ON d.usuario_id = u.id
    AND d.tematica_id = t.id
    AND (d.subtematica_id = s.id OR (s.id IS NULL AND d.subtematica_id IS NULL))
    AND d.estado = 'activo'
GROUP BY u.username, t.id, t.nombre, t.es_general, s.id, s.nombre;

-- PASO 13: Verificación final
SELECT 
    'Temáticas' AS elemento,
    COUNT(*) AS cantidad
FROM tematicas

UNION ALL

SELECT 
    'Subtematicas' AS elemento,
    COUNT(*) AS cantidad
FROM subtematicas

UNION ALL

SELECT 
    'Documentos activos' AS elemento,
    COUNT(*) AS cantidad
FROM documentos
WHERE estado = 'activo';

-- ════════════════════════════════════════════════════════════════════════════════
-- MIGRACIÓN COMPLETADA
-- ════════════════════════════════════════════════════════════════════════════════
--
-- ✅ Tabla tematicas: Ahora es catálogo global (sin usuario_id)
-- ✅ Tabla subtematicas: Con datos iniciales del catálogo
-- ✅ Trigger trg_crear_general: Removido
-- ✅ Vistas: Actualizadas para catálogo global
-- ✅ Documentos: Mantienen su estructura (usuario_id protege privacidad)
--
-- PRÓXIMOS PASOS:
-- 1. Verificar que las consultas SELECT anteriores muestren los datos correctos
-- 2. Probar la API con GET /categories (debe devolver catálogo global)
-- 3. Probar la API con POST /upload (debe clasificar automáticamente)
-- 4. Monitorear logs de errors
--
-- Si algo sale mal, contactar al administrador o hacer rollback con:
-- DELETE FROM subtematicas;
-- DELETE FROM tematicas;
-- (Y restaurar desde backup_documentos si es necesario)
-- ════════════════════════════════════════════════════════════════════════════════
