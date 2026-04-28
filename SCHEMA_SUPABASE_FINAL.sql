-- ══════════════════════════════════════════════════════════════
-- Clasificador Distribuido de Archivos Cientificos
-- Schema final para Supabase / PostgreSQL
-- ══════════════════════════════════════════════════════════════


-- ── 1. ROLES ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT
);

INSERT INTO roles (nombre, descripcion) VALUES
    ('admin', 'Acceso total al sistema y gestion de usuarios'),
    ('user',  'Acceso a su propio espacio de trabajo')
ON CONFLICT (nombre) DO NOTHING;


-- ── 2. USUARIOS ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id        INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    activo        BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo   ON usuarios(activo);


-- ── 3. TOKENS DE SESION ──────────────────────────────────────────────────────
-- CAMBIO 3: expira_en tiene DEFAULT de 24 horas desde la creacion.
-- Python puede sobreescribir este valor si necesita otra duracion.
CREATE TABLE IF NOT EXISTS tokens_sesion (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash  TEXT UNIQUE NOT NULL,
    expira_en   TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '24 hours'),
    revocado    BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tokens_usuario  ON tokens_sesion(usuario_id);
CREATE INDEX IF NOT EXISTS idx_tokens_hash     ON tokens_sesion(token_hash);
CREATE INDEX IF NOT EXISTS idx_tokens_vigentes ON tokens_sesion(revocado, expira_en);


-- ── 4. TEMATICAS (nivel 1) ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tematicas (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre      VARCHAR(150) NOT NULL,
    es_general  BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_tematica_usuario UNIQUE (usuario_id, nombre)
);

CREATE INDEX IF NOT EXISTS idx_tematicas_usuario ON tematicas(usuario_id);


-- ── 5. SUBTEMATICAS (nivel 2) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subtematicas (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tematica_id UUID NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    nombre      VARCHAR(150) NOT NULL,
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_subtematica_tematica UNIQUE (tematica_id, nombre)
);

CREATE INDEX IF NOT EXISTS idx_subtematicas_tematica ON subtematicas(tematica_id);


-- ── 6. DOCUMENTOS ────────────────────────────────────────────────────────────
-- Jerarquia: documento va a tematica DIRECTA (subtematica_id=NULL)
--            o a una SUBtematica (subtematica_id!=NULL, tematica_id=padre)
-- Borrado en 2 pasos: paso 1) estado='eliminando'+eliminado_en
--                     paso 2) CASCADE fisico cuando workers confirman
CREATE TABLE IF NOT EXISTS documentos (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id              UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tematica_id             UUID NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    subtematica_id          UUID REFERENCES subtematicas(id) ON DELETE SET NULL,
    nombre_archivo          VARCHAR(255) NOT NULL,
    hash_original           TEXT,
    tamano_bytes            BIGINT,
    version                 INT NOT NULL DEFAULT 1,
    estado                  VARCHAR(30) NOT NULL DEFAULT 'activo',
    confianza_clasificacion DECIMAL(3,2),
    subido_en               TIMESTAMPTZ NOT NULL DEFAULT now(),
    clasificado_en          TIMESTAMPTZ,
    eliminado_en            TIMESTAMPTZ,

    CONSTRAINT chk_estado CHECK (estado IN ('activo', 'eliminando', 'eliminado'))
);

CREATE INDEX IF NOT EXISTS idx_documentos_usuario     ON documentos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_documentos_tematica    ON documentos(tematica_id);
CREATE INDEX IF NOT EXISTS idx_documentos_subtematica ON documentos(subtematica_id);
CREATE INDEX IF NOT EXISTS idx_documentos_estado      ON documentos(estado);
CREATE INDEX IF NOT EXISTS idx_documentos_hash        ON documentos(hash_original);


-- ── 7. NODOS DE ALMACENAMIENTO ───────────────────────────────────────────────
-- verificado_en se actualiza cuando sync.py confirma que el archivo existe.
CREATE TABLE IF NOT EXISTS nodos_almacenamiento (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id  UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    nodo          VARCHAR(50) NOT NULL,
    ruta_fisica   TEXT NOT NULL,
    activo        BOOLEAN NOT NULL DEFAULT TRUE,
    verificado_en TIMESTAMPTZ,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_nodo_documento UNIQUE (documento_id, nodo)
);

CREATE INDEX IF NOT EXISTS idx_nodos_documento ON nodos_almacenamiento(documento_id);
CREATE INDEX IF NOT EXISTS idx_nodos_nodo      ON nodos_almacenamiento(nodo);


-- ── 8. CONSENSO - VOTOS ──────────────────────────────────────────────────────
-- CAMBIO 1: confianza_worker tiene DEFAULT 0.00 porque classifier.py
-- actualmente usa predict() y no devuelve probabilidades.
-- Cuando se migre a predict_proba() se puede quitar el DEFAULT y
-- pasar a NOT NULL sin valor por defecto.
CREATE TABLE IF NOT EXISTS consenso_votos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id     UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    nodo_worker      VARCHAR(50) NOT NULL,
    area_predicha    VARCHAR(150) NOT NULL,
    confianza_worker DECIMAL(3,2) NOT NULL DEFAULT 0.00,
    ejecutado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_voto_documento_nodo UNIQUE (documento_id, nodo_worker)
);

CREATE INDEX IF NOT EXISTS idx_votos_documento ON consenso_votos(documento_id);
CREATE INDEX IF NOT EXISTS idx_votos_worker    ON consenso_votos(nodo_worker);


-- ── 9. LIDER ACTUAL ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lider_actual (
    id                 INT PRIMARY KEY DEFAULT 1,
    nodo_id            INT NOT NULL,
    nodo_hostname      TEXT NOT NULL,
    nodo_url           TEXT NOT NULL,
    heartbeat_interval INT NOT NULL DEFAULT 5,
    elegido_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_heartbeat   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT una_sola_fila CHECK (id = 1)
);

INSERT INTO lider_actual (id, nodo_id, nodo_hostname, nodo_url)
VALUES (1, 0, 'sin-lider', '')
ON CONFLICT DO NOTHING;


-- ══════════════════════════════════════════════════════════════
-- TRIGGERS
-- ══════════════════════════════════════════════════════════════

-- Al registrar un usuario, crear su tematica 'General' automaticamente
CREATE OR REPLACE FUNCTION crear_tematica_general()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO tematicas (usuario_id, nombre, es_general)
    VALUES (NEW.id, 'General', TRUE)
    ON CONFLICT DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_crear_general ON usuarios;
CREATE TRIGGER trg_crear_general
AFTER INSERT ON usuarios
FOR EACH ROW EXECUTE FUNCTION crear_tematica_general();


-- Al actualizar lider_actual, refrescar ultimo_heartbeat automaticamente
CREATE OR REPLACE FUNCTION actualizar_heartbeat()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultimo_heartbeat = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_heartbeat ON lider_actual;
CREATE TRIGGER trg_heartbeat
BEFORE UPDATE ON lider_actual
FOR EACH ROW EXECUTE FUNCTION actualizar_heartbeat();


-- ══════════════════════════════════════════════════════════════
-- VISTAS
-- ══════════════════════════════════════════════════════════════

-- Arbol de clasificacion por usuario con conteo de documentos
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
JOIN tematicas    t ON t.usuario_id = u.id
LEFT JOIN subtematicas s ON s.tematica_id = t.id
LEFT JOIN documentos   d ON d.tematica_id = t.id
    AND (d.subtematica_id = s.id OR (s.id IS NULL AND d.subtematica_id IS NULL))
    AND d.estado = 'activo'
GROUP BY u.username, t.id, t.nombre, t.es_general, s.id, s.nombre;


-- Resumen de un documento con sus votos y nodos de replica
CREATE OR REPLACE VIEW vista_documento_completo AS
SELECT
    d.id,
    d.nombre_archivo,
    u.username,
    t.nombre     AS tematica,
    s.nombre     AS subtematica,
    d.confianza_clasificacion,
    d.estado,
    d.tamano_bytes,
    COUNT(DISTINCT cv.nodo_worker)  AS workers_que_votaron,
    COUNT(DISTINCT na.nodo)         AS nodos_con_replica,
    d.subido_en,
    d.clasificado_en
FROM documentos d
JOIN usuarios  u  ON u.id = d.usuario_id
JOIN tematicas t  ON t.id = d.tematica_id
LEFT JOIN subtematicas         s  ON s.id  = d.subtematica_id
LEFT JOIN consenso_votos       cv ON cv.documento_id = d.id
LEFT JOIN nodos_almacenamiento na ON na.documento_id = d.id
WHERE d.estado = 'activo'
GROUP BY d.id, u.username, t.nombre, s.nombre;


-- Sesiones activas no expiradas ni revocadas
CREATE OR REPLACE VIEW vista_sesiones_activas AS
SELECT
    u.username,
    t.token_hash,
    t.expira_en,
    t.creado_en,
    (t.expira_en - now())::text AS tiempo_restante
FROM tokens_sesion t
JOIN usuarios u ON u.id = t.usuario_id
WHERE t.revocado = FALSE
  AND t.expira_en > now();


-- Estado del lider con diagnostico de salud
CREATE OR REPLACE VIEW vista_estado_lider AS
SELECT
    nodo_id,
    nodo_hostname,
    nodo_url,
    elegido_en,
    ultimo_heartbeat,
    now() - ultimo_heartbeat AS tiempo_sin_heartbeat,
    CASE
        WHEN (now() - ultimo_heartbeat) < make_interval(secs := heartbeat_interval * 3)
        THEN 'VIVO'
        ELSE 'CAIDO'
    END AS estado
FROM lider_actual
WHERE id = 1;


-- ══════════════════════════════════════════════════════════════
-- FASES FUTURAS (no implementadas aun)
-- ══════════════════════════════════════════════════════════════

-- FASE FUTURA - Cuotas por usuario
-- CREATE TABLE IF NOT EXISTS cuotas_usuario (
--     usuario_id               UUID PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
--     limite_documentos        INT NOT NULL DEFAULT 1000,
--     limite_almacenamiento_mb INT NOT NULL DEFAULT 10000,
--     documentos_procesados    INT NOT NULL DEFAULT 0,
--     almacenamiento_usado_mb  INT NOT NULL DEFAULT 0,
--     actualizado_en           TIMESTAMPTZ NOT NULL DEFAULT now()
-- );

-- FASE FUTURA - Logs de errores de clasificacion
-- CREATE TABLE IF NOT EXISTS logs_errores_clasificacion (
--     id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     documento_id  UUID REFERENCES documentos(id) ON DELETE CASCADE,
--     nodo_worker   VARCHAR(50),
--     tipo_error    VARCHAR(100),
--     mensaje_error TEXT,
--     trazabilidad  JSONB,
--     registrado_en TIMESTAMPTZ NOT NULL DEFAULT now()
-- );


-- ══════════════════════════════════════════════════════════════════════════════
-- Ahora:
-- 1. Ve a master/database.py (ya está actualizado)
-- 2. Configura variables de entorno en .env
-- 3. Prueba: python -m pytest tests/test_database.py
-- ══════════════════════════════════════════════════════════════════════════════
