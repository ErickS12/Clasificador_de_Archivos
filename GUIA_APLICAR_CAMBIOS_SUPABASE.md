# 📋 Guía: Aplicar Cambios en Supabase

## 🚨 SITUACIÓN ACTUAL

| Elemento | Estado Local | Estado Supabase |
|----------|--------------|-----------------|
| Archivo SQL | ✅ ACTUALIZADO (catálogo global) | ❌ DESACTUALIZADO (por usuario) |
| Python code | ✅ ACTUALIZADO | - |
| Workers | ✅ ACTUALIZADO | - |
| Base de Datos | ❌ DESINCRONIZADA | Contiene estructura vieja |

**Acción necesaria:** Aplicar la migración en Supabase para sincronizar con el código.

---

## 📝 PASOS PARA APLICAR LA MIGRACIÓN

### 1️⃣ HACER BACKUP (⚠️ CRÍTICO)

```bash
# Opción A: Supabase Dashboard
# 1. Ve a: https://app.supabase.com
# 2. Selecciona tu proyecto
# 3. SQL Editor → "Create a new query"
# 4. Copia y ejecuta:

SELECT * FROM documentos LIMIT 1;
SELECT * FROM tematicas LIMIT 5;
-- Si devuelve resultados, tu BD tiene datos
```

**Recomendación:** Hacer backup manual:
- Descargar CSV de tablas importantes desde Supabase Dashboard
- O ejecutar: `pg_dump` si tienes acceso directo

---

### 2️⃣ EJECUTAR LA MIGRACIÓN

#### **Opción A: Supabase SQL Editor (Recomendado)**

```
1. Abre: https://app.supabase.com/project/[tu-proyecto]/sql/new
2. Copia TODO el contenido de: MIGRACION_CATALOGO_GLOBAL.sql
3. Pega en el editor
4. Presiona: "Run" (botón azul)
5. Espera a que complete
```

#### **Opción B: Desde terminal (Si tienes psql instalado)**

```bash
# Configurar variables de entorno
export PGPASSWORD="tu-password-supabase"

# Ejecutar migración
psql -h "db.tu-proyecto.supabase.co" \
     -U "postgres" \
     -d "postgres" \
     -f MIGRACION_CATALOGO_GLOBAL.sql
```

---

### 3️⃣ VERIFICAR LA MIGRACIÓN

Después de ejecutar, deberías ver algo como:

```
elemento              | cantidad
----------------------------------
Temáticas             | 3
Subtematicas          | 8
Documentos activos    | 0 (o más si hay datos)
```

**Si ves esto:** ✅ **Migración exitosa**

---

### 4️⃣ PROBAR QUE TODO FUNCIONA

#### **Test 1: Verificar catálogo global**

```bash
# Terminal
curl -X GET http://localhost:8000/categories \
  -H "Authorization: Bearer [tu-token]"

# Respuesta esperada:
{
  "categorias_globales": [
    "Tecnología/Inteligencia Artificial",
    "Tecnología/Redes",
    "Tecnología/Bases de Datos",
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
  "clasificado_en": "Tecnología/Redes",  # Clasificado automáticamente
  "replicado_en": ["node1", "node2", "node3"],
  "consenso": {...}
}
```

---

## ⚠️ POSIBLES PROBLEMAS Y SOLUCIONES

### Problema 1: "Column usuario_id does not exist"
```
❌ ERROR: column "usuario_id" does not exist
```

**Causa:** Vistas antiguas aún hacen referencia a usuario_id

**Solución:**
```sql
DROP VIEW IF EXISTS vista_arbol_usuario CASCADE;
DROP VIEW IF EXISTS vista_documento_completo CASCADE;
-- Luego ejecutar la migración de nuevo
```

---

### Problema 2: "Foreign key constraint violated"
```
❌ ERROR: insert or update on table "documentos" violates foreign key constraint
```

**Causa:** Documentos viejos referencia tematicas que se borraron

**Solución:**
```sql
-- Mover documentos viejos a "Otros/General"
UPDATE documentos 
SET tematica_id = (SELECT id FROM tematicas WHERE nombre = 'Otros')
WHERE tematica_id NOT IN (SELECT id FROM tematicas);
```

---

### Problema 3: "Uniqueness violation" en nombre de tematica
```
❌ ERROR: duplicate key value violates unique constraint "uq_tematica_nombre"
```

**Causa:** Intentar insertar categoría que ya existe

**Solución:** Ya está en el script `ON CONFLICT (nombre) DO NOTHING`
- Simplemente ejecutar la migración de nuevo

---

## 📊 VERIFICACIÓN DETALLADA

Ejecuta estas queries para verificar todo:

```sql
-- Ver catálogo global
SELECT id, nombre, es_general FROM tematicas;

-- Ver subcategorías
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

## 🔄 ROLLBACK (Si algo sale mal)

Si necesitas volver atrás:

```sql
-- OPCIÓN 1: Restaurar desde backup (recomendado)
-- Usa Supabase Dashboard → Backups → Restore

-- OPCIÓN 2: Manual (si no tienes backup)
-- Eliminar nuevas categorías y restaurar viejas
DELETE FROM subtematicas WHERE id IN (
    SELECT s.id FROM subtematicas s
    JOIN tematicas t ON t.id = s.tematica_id
    WHERE t.nombre IN ('Tecnología', 'Ciencias', 'Otros')
);

DELETE FROM tematicas WHERE nombre IN ('Tecnología', 'Ciencias', 'Otros');
-- Luego restaurar datos anteriores desde backup_documentos
```

---

## ✅ CHECKLIST POST-MIGRACIÓN

- [ ] Migración ejecutada sin errores
- [ ] SELECT de verificación devuelve resultados correctos
- [ ] GET /categories devuelve catálogo global
- [ ] POST /upload clasifica automáticamente
- [ ] GET /files muestra documentos del usuario
- [ ] Logs no muestran errores de FK
- [ ] Prueba con 2-3 PDFs
- [ ] Revisar consenso en logs (3 workers prediciendo)

---

## 📞 SOPORTE

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

## 🎓 RESUMEN DEL CAMBIO

**ANTES:**
```
Usuario A
├─ Mi Área 1
│  ├─ Subárea A
│  └─ Subárea B
└─ Mi Área 2

Usuario B
└─ Su Área
```

**AHORA:**
```
CATÁLOGO GLOBAL (igual para todos)
├─ Tecnología
│  ├─ Inteligencia Artificial
│  ├─ Redes
│  └─ Bases de Datos
├─ Ciencias
│  ├─ Biología
│  └─ Matemáticas
└─ Otros
   └─ General

Los documentos de cada usuario se clasifican automáticamente aquí.
Cada usuario solo ve sus propios documentos (usuario_id).
```

---

**¿Listo?** 🚀 Ejecuta la migración ahora!
