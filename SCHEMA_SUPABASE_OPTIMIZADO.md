# Schema Supabase â€” AnÃ¡lisis & Recomendaciones

## âœ… VEREDICTO: El schema nuevo es **100% mejor** que el stub

---

## ðŸ”§ CAMBIOS RECOMENDADOS al Schema Nuevo

### 1. â­ AGREGAR: Tabla de AuditorÃ­a

```sql
-- Rastrear cambios en documentos (quiÃ©n clasificÃ³, cuÃ¡ndo, quÃ© consenso)
CREATE TABLE auditoria_documentos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id    UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    usuario_id      UUID NOT NULL REFERENCES usuarios(id) ON DELETE SET NULL,
    accion          VARCHAR(50) NOT NULL, -- 'clasificacion', 'reclasificacion', 'eliminacion'
    area_anterior   VARCHAR(150),
    area_nueva      VARCHAR(150),
    confianza       DECIMAL(3,2),  -- 0.67-1.0 (mayorÃ­a)
    realizado_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_auditoria_documento ON auditoria_documentos(documento_id);
```

**Por quÃ©**: Necesitas trazar por quÃ© un documento terminÃ³ en una categorÃ­a (debugging).

---

### 2. â­ AGREGAR: Tabla de SincronizaciÃ³n de Nodos

```sql
-- Rastrear quÃ© nodo tiene quÃ© archivo (para replicaciÃ³n)
CREATE TABLE sincronizacion_nodos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id    UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    nodo            VARCHAR(50) NOT NULL,
    hash_archivo    TEXT,        -- SHA256 para verificaciÃ³n de integridad
    tamaÃ±o_bytes    BIGINT,
    sincronizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    verificado_en   TIMESTAMPTZ
);

CREATE INDEX idx_sync_documento ON sincronizacion_nodos(documento_id);
CREATE INDEX idx_sync_nodo ON sincronizacion_nodos(nodo);
```

**Por quÃ©**: Para validar que los 3 nodos tienen copias idÃ©nticas (tolerancia a fallos).

---

### 3. â­ MEJORAR: Tabla `documentos`

**Cambio propuesto**:

```sql
-- VersiÃ³n mejorada
CREATE TABLE documentos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id       UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tematica_id      UUID NOT NULL REFERENCES tematicas(id) ON DELETE CASCADE,
    subtematica_id   UUID REFERENCES subtematicas(id) ON DELETE SET NULL,
    nombre_archivo   VARCHAR(255) NOT NULL,
    hash_original    TEXT,              -- SHA256 del PDF original
    tamaÃ±o_bytes     BIGINT,            -- TamaÃ±o del archivo
    paginas          INT,               -- NÃºmero de pÃ¡ginas
    version          INT NOT NULL DEFAULT 1,
    estado           VARCHAR(30) NOT NULL DEFAULT 'activo', -- 'activo', 'eliminado', 'reclasificando'
    confianza_clasificacion DECIMAL(3,2),  -- 0.67-1.0
    subido_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
    clasificado_en   TIMESTAMPTZ,
    eliminado_en     TIMESTAMPTZ
);

CREATE INDEX idx_documentos_usuario     ON documentos(usuario_id);
CREATE INDEX idx_documentos_tematica    ON documentos(tematica_id);
CREATE INDEX idx_documentos_subtematica ON documentos(subtematica_id);
CREATE INDEX idx_documentos_estado      ON documentos(estado);
```

**Por quÃ©**:
- `hash_original`: Permite detectar si alguien resubiÃ³ el mismo archivo
- `paginas`, `tamaÃ±o_bytes`: Para estadÃ­sticas y lÃ­mites de quota
- `estado`: Mejor que `eliminado_en` para tracking de reclasificaciones
- `confianza_clasificacion`: Para mostrar al usuario quÃ© tan segura es la categorizaciÃ³n

---

### 4. â­ MEJORAR: Tabla `consenso_votos`

**Cambio propuesto**:

```sql
-- VersiÃ³n mejorada
CREATE TABLE consenso_votos (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id     UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    nodo_worker      VARCHAR(50) NOT NULL,  -- RenombrÃ©: 'nodo' â†’ 'nodo_worker'
    area_predicha    VARCHAR(150) NOT NULL,
    confianza_worker DECIMAL(3,2) NOT NULL,  -- Confianza del worker individual
    ejecutado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT uq_voto_documento_nodo UNIQUE (documento_id, nodo_worker)
);

CREATE INDEX idx_votos_documento ON consenso_votos(documento_id);
```

**Por quÃ©**:
- `nodo_worker`: Clarifica que es el worker (no el nodo de almacenamiento)
- `confianza_worker`: Para debugging de workers divergentes
- Quitamos `area_votada` duplicado y `disponible` (eso estÃ¡ en nodos_almacenamiento)

---

### 5. â­ MEJORAR: Tabla `nodos_almacenamiento`

**VersiÃ³n clara**:

```sql
-- Nodos de replicaciÃ³n (storage/node1-3/)
CREATE TABLE nodos_almacenamiento (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id    UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    nodo            VARCHAR(50) NOT NULL,  -- 'node1', 'node2', 'node3'
    ruta_fisica     TEXT NOT NULL,         -- Relativa a storage/ o absoluta
    md5_archivo     TEXT,                  -- Para verificaciÃ³n post-escritura
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT uq_nodo_documento UNIQUE (documento_id, nodo)
);

CREATE INDEX idx_nodos_documento ON nodos_almacenamiento(documento_id);
CREATE INDEX idx_nodos_nodo ON nodos_almacenamiento(nodo);
```

**Nota**: Mantener esta tabla pero sincronizar con sincronizacion_nodos.

---

### 6. â­ AGREGAR: Tabla de Cuotas/LÃ­mites de Usuario

```sql
CREATE TABLE cuotas_usuario (
    usuario_id              UUID PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    limite_documentos       INT NOT NULL DEFAULT 1000,
    limite_almacenamiento_mb INT NOT NULL DEFAULT 10000,  -- 10 GB
    reclasificaciones_diarias INT NOT NULL DEFAULT 50,
    documentos_procesados   INT NOT NULL DEFAULT 0,
    almacenamiento_usado_mb INT NOT NULL DEFAULT 0,
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cuota_usuario ON cuotas_usuario(usuario_id);
```

---

### 7. â­ MEJORAR: Tabla `lider_actual`

**VersiÃ³n mejorada**:

```sql
-- Control de consenso del cluster
CREATE TABLE lider_actual (
    id                  INT PRIMARY KEY DEFAULT 1,
    nodo_id             INT NOT NULL,
    nodo_hostname       TEXT NOT NULL,     -- 'master', 'worker1', 'worker2', 'worker3'
    nodo_url            TEXT NOT NULL,     -- 'http://localhost:5000'
    elegido_en          TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_heartbeat    TIMESTAMPTZ NOT NULL DEFAULT now(),
    heartbeat_interval  INT DEFAULT 5,     -- segundos
    
    CONSTRAINT una_sola_fila CHECK (id = 1)
);

CREATE TRIGGER trg_actualizar_heartbeat
BEFORE UPDATE ON lider_actual
FOR EACH ROW
SET NEW.ultimo_heartbeat = now();
```

---

### 8. â­ AGREGAR: Tabla de Logs de Errores

```sql
CREATE TABLE logs_errores_clasificacion (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id    UUID REFERENCES documentos(id) ON DELETE CASCADE,
    nodo_worker     VARCHAR(50),
    tipo_error      VARCHAR(100),   -- 'timeout', 'clasificacion_fallida', 'pdf_invalido'
    mensaje_error   TEXT,
    trazabilidad    JSONB,          -- {worker_response, payload, timestamp}
    registrado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_errores_documento ON logs_errores_clasificacion(documento_id);
```

---

## ðŸ“‹ VISTAS RECOMENDADAS

Tu schema ya tiene 3 vistas; sugiero agregar:

```sql
-- Vista: Estado completo de un documento
CREATE OR REPLACE VIEW vista_documento_completo AS
SELECT
    d.id,
    d.nombre_archivo,
    u.username,
    t.nombre AS tematica,
    s.nombre AS subtematica,
    d.confianza_clasificacion,
    d.estado,
    COUNT(DISTINCT cv.nodo_worker) AS workers_clasificados,
    COUNT(DISTINCT na.nodo) AS nodos_replicados,
    d.subido_en,
    d.clasificado_en
FROM documentos d
JOIN usuarios u ON u.id = d.usuario_id
JOIN tematicas t ON t.id = d.tematica_id
LEFT JOIN subtematicas s ON s.id = d.subtematica_id
LEFT JOIN consenso_votos cv ON cv.documento_id = d.id
LEFT JOIN nodos_almacenamiento na ON na.documento_id = d.id
WHERE d.eliminado_en IS NULL
GROUP BY d.id, u.username, t.nombre, s.nombre;

-- Vista: Salud del cluster
CREATE OR REPLACE VIEW vista_salud_cluster AS
SELECT
    nodo,
    COUNT(*) AS documentos_replicados,
    MAX(creado_en) AS ultima_replicacion
FROM nodos_almacenamiento
WHERE activo = TRUE
GROUP BY nodo;
```

---

## ðŸ”„ MAPPING CON CÃ“DIGO EXISTENTE

### En `database.py` necesitarÃ­as funciones como:

```python
# Funciones que el gateway necesita
def insertar_documento(usuario_id, tematica_id, subtematica_id, nombre_archivo, hash_archivo, tamaÃ±o):
    """Crea registro en documentos + cuota_usuario"""
    pass

def insertar_voto_consenso(documento_id, nodo_worker, area_predicha, confianza):
    """Registra voto de cada worker"""
    pass

def insertar_nodo_replicacion(documento_id, nodo, ruta_fisica):
    """Registra dÃ³nde se replicÃ³ el archivo"""
    pass

def registrar_auditoria(documento_id, usuario_id, accion, area_anterior, area_nueva, confianza):
    """AuditorÃ­a de cambios"""
    pass

def actualizar_heartbeat_lider(nodo_id):
    """Keep-alive del liderazgo"""
    pass
```

---

## âœ¨ RESUMEN: Cambios CrÃ­ticos

| Tabla | Cambio | Prioridad |
|-------|--------|-----------|
| `documentos` | Agregar `hash_original`, `paginas`, `estado`, `confianza_clasificacion` | ðŸ”´ Alta |
| `consenso_votos` | Renombrar `nodo` â†’ `nodo_worker`, agregar `confianza_worker` | ðŸŸ¡ Media |
| â€” | **AGREGAR** `auditoria_documentos` | ðŸ”´ Alta |
| â€” | **AGREGAR** `sincronizacion_nodos` | ðŸŸ¡ Media |
| â€” | **AGREGAR** `cuotas_usuario` | ðŸŸ¡ Media |
| `lider_actual` | Agregar `heartbeat_interval`, trigger de timestamp | ðŸŸ¢ Baja |
| â€” | **AGREGAR** `logs_errores_clasificacion` | ðŸŸ¢ Baja |

---

## ðŸŽ¯ CONCLUSIÃ“N

**El schema nuevo es infinitamente mejor** que el stub de database.py porque:

1. âœ… Normaliza roles, tokens, jerarquÃ­a
2. âœ… Hace explicito lo que estaba implÃ­cito en JSON
3. âœ… Permite auditorÃ­a y debugging
4. âœ… Soporta replicaciÃ³n distribuida
5. âœ… Tiene triggers inteligentes

**Con los cambios propuestos arriba**, tendrÃ­as un schema listo para producciÃ³n.

