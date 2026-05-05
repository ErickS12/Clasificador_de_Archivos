# ðŸ“‹ GuÃ­a: Aplicar Cambios en Supabase

## ðŸš¨ SITUACIÃ“N ACTUAL

| Elemento | Estado Local | Estado Supabase |
|----------|--------------|-----------------|
| Archivo SQL | âœ… ACTUALIZADO (catÃ¡logo global) | âŒ DESACTUALIZADO (por usuario) |
| Python code | âœ… ACTUALIZADO | - |
| Workers | âœ… ACTUALIZADO | - |
| Base de Datos | âŒ DESINCRONIZADA | Contiene estructura vieja |

**AcciÃ³n necesaria:** Aplicar la migraciÃ³n en Supabase para sincronizar con el cÃ³digo.

---

## ðŸ“ PASOS PARA APLICAR LA MIGRACIÃ“N

### 1ï¸âƒ£ HACER BACKUP (âš ï¸ CRÃTICO)

```bash
# OpciÃ³n A: Supabase Dashboard
# 1. Ve a: https://app.supabase.com
# 2. Selecciona tu proyecto
# 3. SQL Editor â†’ "Create a new query"
# 4. Copia y ejecuta:

SELECT * FROM documentos LIMIT 1;
SELECT * FROM tematicas LIMIT 5;
-- Si devuelve resultados, tu BD tiene datos
```

**RecomendaciÃ³n:** Hacer backup manual:
- Descargar CSV de tablas importantes desde Supabase Dashboard
- O ejecutar: `pg_dump` si tienes acceso directo

---

### 2ï¸âƒ£ EJECUTAR LA MIGRACIÃ“N

#### **OpciÃ³n A: Supabase SQL Editor (Recomendado)**

```
1. Abre: https://app.supabase.com/project/[tu-proyecto]/sql/new
2. Copia TODO el contenido de: MIGRACION_CATALOGO_GLOBAL.sql
3. Pega en el editor
4. Presiona: "Run" (botÃ³n azul)
5. Espera a que complete
```

#### **OpciÃ³n B: Desde terminal (Si tienes psql instalado)**

```bash
# Configurar variables de entorno
export PGPASSWORD="tu-password-supabase"

# Ejecutar migraciÃ³n
psql -h "db.tu-proyecto.supabase.co" \
     -U "postgres" \
     -d "postgres" \
     -f MIGRACION_CATALOGO_GLOBAL.sql
```

---

### 3ï¸âƒ£ VERIFICAR LA MIGRACIÃ“N

DespuÃ©s de ejecutar, deberÃ­as ver algo como:

```
elemento              | cantidad
----------------------------------
TemÃ¡ticas             | 3
Subtematicas          | 8
Documentos activos    | 0 (o mÃ¡s si hay datos)
```

**Si ves esto:** âœ… **MigraciÃ³n exitosa**

---

### 4ï¸âƒ£ PROBAR QUE TODO FUNCIONA

#### **Test 1: Verificar catÃ¡logo global**

```bash
# Terminal
curl -X GET http://localhost:8000/categories \
  -H "Authorization: Bearer [tu-token]"

# Respuesta esperada:
{
  "categorias_globales": [
    "TecnologÃ­a/Inteligencia Artificial",
    "TecnologÃ­a/Redes",
    "TecnologÃ­a/Bases de Datos",
    ...
  ]
}
```

#### **Test 2: Subir un archivo**

```bash
# Terminal
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer [tu-token]" \
  -F "archivo=@paper.pdf"

# Respuesta esperada:
{
  "archivo": "paper.pdf",
  "clasificado_en": "TecnologÃ­a/Redes",  # Clasificado automÃ¡ticamente
  "replicado_en": ["node1", "node2", "node3"],
  "consenso": {...}
}
```

---

## âš ï¸ POSIBLES PROBLEMAS Y SOLUCIONES

### Problema 1: "Column usuario_id does not exist"
```
âŒ ERROR: column "usuario_id" does not exist
```

**Causa:** Vistas antiguas aÃºn hacen referencia a usuario_id

**SoluciÃ³n:**
```sql
DROP VIEW IF EXISTS vista_arbol_usuario CASCADE;
DROP VIEW IF EXISTS vista_documento_completo CASCADE;
-- Luego ejecutar la migraciÃ³n de nuevo
```

---

### Problema 2: "Foreign key constraint violated"
```
âŒ ERROR: insert or update on table "documentos" violates foreign key constraint
```

**Causa:** Documentos viejos referencia tematicas que se borraron

**SoluciÃ³n:**
```sql
-- Mover documentos viejos a "Otros/General"
UPDATE documentos 
SET tematica_id = (SELECT id FROM tematicas WHERE nombre = 'Otros')
WHERE tematica_id NOT IN (SELECT id FROM tematicas);
```

---

### Problema 3: "Uniqueness violation" en nombre de tematica
```
âŒ ERROR: duplicate key value violates unique constraint "uq_tematica_nombre"
```

**Causa:** Intentar insertar categorÃ­a que ya existe

**SoluciÃ³n:** Ya estÃ¡ en el script `ON CONFLICT (nombre) DO NOTHING`
- Simplemente ejecutar la migraciÃ³n de nuevo

---

## ðŸ“Š VERIFICACIÃ“N DETALLADA

Ejecuta estas queries para verificar todo:

```sql
-- Ver catÃ¡logo global
SELECT id, nombre, es_general FROM tematicas;

-- Ver subcategorÃ­as
SELECT t.nombre AS tematica, s.nombre AS subtematica 
FROM subtematicas s
JOIN tematicas t ON t.id = s.tematica_id
ORDER BY t.nombre, s.nombre;

-- Ver documentos
SELECT COUNT(*) as total_documentos FROM documentos WHERE estado = 'activo';

-- Ver si hay vistas rotas
SELECT * FROM vista_arbol_usuario LIMIT 1;
```

---

## ðŸ”„ ROLLBACK (Si algo sale mal)

Si necesitas volver atrÃ¡s:

```sql
-- OPCIÃ“N 1: Restaurar desde backup (recomendado)
-- Usa Supabase Dashboard â†’ Backups â†’ Restore

-- OPCIÃ“N 2: Manual (si no tienes backup)
-- Eliminar nuevas categorÃ­as y restaurar viejas
DELETE FROM subtematicas WHERE id IN (
    SELECT s.id FROM subtematicas s
    JOIN tematicas t ON t.id = s.tematica_id
    WHERE t.nombre IN ('TecnologÃ­a', 'Ciencias', 'Otros')
);

DELETE FROM tematicas WHERE nombre IN ('TecnologÃ­a', 'Ciencias', 'Otros');
-- Luego restaurar datos anteriores desde backup_documentos
```

---

## âœ… CHECKLIST POST-MIGRACIÃ“N

- [ ] MigraciÃ³n ejecutada sin errores
- [ ] SELECT de verificaciÃ³n devuelve resultados correctos
- [ ] GET /categories devuelve catÃ¡logo global
- [ ] POST /upload clasifica automÃ¡ticamente
- [ ] GET /files muestra documentos del usuario
- [ ] Logs no muestran errores de FK
- [ ] Prueba con 2-3 PDFs
- [ ] Revisar consenso en logs (3 workers prediciendo)

---

## ðŸ“ž SOPORTE

Si tienes problemas:

1. **Verifica los logs:**
   ```bash
   # En terminal del maestro
   tail -f logs/master.log
   
   # En terminal de workers
   tail -f logs/worker1.log
   ```

2. **Revisa la tabla documentos:**
   ```sql
   SELECT COUNT(*) FROM documentos WHERE estado = 'activo';
   ```

3. **Contacta al equipo con:**
   - Error exacto que ves
   - Nombre del proyecto Supabase
   - Logs completos

---

## ðŸŽ“ RESUMEN DEL CAMBIO

**ANTES:**
```
Usuario A
â”œâ”€ Mi Ãrea 1
â”‚  â”œâ”€ SubÃ¡rea A
â”‚  â””â”€ SubÃ¡rea B
â””â”€ Mi Ãrea 2

Usuario B
â””â”€ Su Ãrea
```

**AHORA:**
```
CATÃLOGO GLOBAL (igual para todos)
â”œâ”€ TecnologÃ­a
â”‚  â”œâ”€ Inteligencia Artificial
â”‚  â”œâ”€ Redes
â”‚  â””â”€ Bases de Datos
â”œâ”€ Ciencias
â”‚  â”œâ”€ BiologÃ­a
â”‚  â””â”€ MatemÃ¡ticas
â””â”€ Otros
   â””â”€ General

Los documentos de cada usuario se clasifican automÃ¡ticamente aquÃ­.
Cada usuario solo ve sus propios documentos (usuario_id).
```

---

**Â¿Listo?** ðŸš€ Ejecuta la migraciÃ³n ahora!

