-- ══════════════════════════════════════════════════
-- Tabla: lider_actual
-- Pegar en SQL Editor de Supabase y ejecutar
-- ══════════════════════════════════════════════════

CREATE TABLE lider_actual (
    id                INT PRIMARY KEY DEFAULT 1,
    nodo_id           INT NOT NULL,
    nodo_url          TEXT NOT NULL,
    elegido_en        TIMESTAMPTZ DEFAULT now(),
    ultimo_heartbeat  TIMESTAMPTZ DEFAULT now(),

    -- Garantiza que siempre haya exactamente una fila
    CONSTRAINT una_sola_fila CHECK (id = 1)
);

-- Fila inicial vacía (necesaria para el primer upsert)
INSERT INTO lider_actual (id, nodo_id, nodo_url)
VALUES (1, 0, '')
ON CONFLICT DO NOTHING;

-- ══════════════════════════════════════════════════
-- Vista opcional: ver estado del clúster en tiempo real
-- ══════════════════════════════════════════════════

CREATE OR REPLACE VIEW estado_cluster AS
SELECT
    nodo_id,
    nodo_url,
    elegido_en,
    ultimo_heartbeat,
    now() - ultimo_heartbeat AS tiempo_sin_heartbeat
FROM lider_actual
WHERE id = 1;
