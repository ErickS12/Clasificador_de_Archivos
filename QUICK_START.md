# 🚀 GUÍA RÁPIDA: Los 5 Pasos Finales

**Tiempo total: ~40 minutos**

---

## ⏱️ PASO 1: LEE (5 MIN)

Lee este archivo primero para entender qué va a pasar:

```
📄 COMPARACION_SCHEMA_ANTES_DESPUES.md
   ↓
   Entenderás qué cambia en la BD
```

---

## 💾 PASO 2: BACKUP (5 MIN)

**MÁS IMPORTANTE ANTES DE TOCAR LA BD**

### Opción A: Supabase Dashboard (Recomendado)
```
1. Ve a: https://app.supabase.com
2. Selecciona tu proyecto
3. Settings → Backups → Create backup
4. Espera a que se complete
```

### Opción B: Exportar datos (Como respaldo adicional)
```
1. Ve a SQL Editor en Supabase
2. Ejecuta:
   SELECT * FROM tematicas;
   SELECT * FROM subtematicas;
   SELECT * FROM documentos;
3. Descarga como CSV
```

---

## 🗄️ PASO 3: MIGRACIÓN SQL (2 MIN)

**Ejecutar en Supabase:**

```
1. Abre: https://app.supabase.com/project/[TU-PROYECTO]/sql/new
2. Abre el archivo: MIGRACION_CATALOGO_GLOBAL.sql (en tu carpeta)
3. Copia TODO el contenido
4. Pégalo en Supabase SQL Editor
5. Presiona: "Run" (botón azul)
6. Espera a que complete (toma ~30 segundos)
```

**Debería ver algo como:**
```
✅ CREATE TABLE
✅ INSERT 3 rows into tematicas
✅ INSERT 8 rows into subtematicas
✅ DROP TRIGGER
✅ CREATE VIEW
✅ SELECT (resultados de verificación)
```

---

## 🤖 PASO 4: ENTRENAR MODELO (5-10 MIN)

**En tu terminal local:**

```bash
cd c:\Clasificador_de_Archivos
python worker/entrenar_modelo.py
```

**Debería ver:**
```
Loading training data...
Training model (hierarchical labels)...
TF-IDF Vectorizer trained with 6 categories
LogisticRegression trained with 6 labels
Model saved to: worker/modelo_clasificador.pkl
Training complete!
```

---

## ✅ PASO 5: VERIFICAR (10 MIN)

### 5.1: Verificar estructura en Supabase
```sql
-- Copiar y ejecutar en Supabase SQL Editor

-- Ver tematicas globales
SELECT id, nombre FROM tematicas;
-- Esperado: 3 filas (Tecnología, Ciencias, Otros)

-- Ver subtematicas
SELECT t.nombre AS tematica, s.nombre AS subtematica
FROM subtematicas s
JOIN tematicas t ON t.id = s.tematica_id
ORDER BY t.nombre, s.nombre;
-- Esperado: 8 filas

-- Verificar que NO hay usuario_id
SELECT column_name FROM information_schema.columns
WHERE table_name = 'tematicas';
-- NO debe aparecer usuario_id ✓
```

### 5.2: Probar API (desde terminal)

```bash
# Verificar que servidor está corriendo
# Terminal 1:
cd c:\Clasificador_de_Archivos
python master/main.py

# Terminal 2:
cd c:\Clasificador_de_Archivos
python worker/main.py

# Terminal 3: Pruebas
# Prueba 1: Ver catálogo global
curl -X GET http://localhost:8000/categories

# Esperado:
# {
#   "categorias_globales": [
#     "Tecnología/Inteligencia Artificial",
#     "Tecnología/Redes",
#     "Tecnología/Bases de Datos",
#     "Tecnología/Sistemas Operativos",
#     "Tecnología/Sistemas Distribuidos",
#     "Ciencias/Biología",
#     "Ciencias/Matemáticas",
#     "Otros/General"
#   ]
# }

# Prueba 2: Subir PDF
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer test-token" \
  -F "archivo=@test.pdf"

# Debería clasificar automáticamente con consenso de 3 workers
```

---

## ✅ CHECKLIST POST-MIGRACIÓN

```
Después de completar los 5 pasos, verificar:

Base de Datos:
  ☐ Tabla tematicas tiene 3 registros (sin usuario_id)
  ☐ Tabla subtematicas tiene 8 registros
  ☐ Vista vista_arbol_usuario funciona sin errores
  ☐ NO hay columna usuario_id en tematicas

Modelo:
  ☐ Archivo worker/modelo_clasificador.pkl fue creado
  ☐ Size > 1KB (no está vacío)

API:
  ☐ GET /categories devuelve 8 categorías globales
  ☐ POST /upload clasifica automáticamente
  ☐ Logs muestran: "3/3 workers agree" (consenso)
  ☐ No hay errores de "foreign key" en logs

Testing:
  ☐ Probé con 1+ PDF
  ☐ Subí archivo con usuario autenticado
  ☐ Descargué archivo subido
  ☐ Clasificación fue automática
```

---

## 🆘 SI ALGO SALE MAL

### Error: "Column usuario_id does not exist"
```
→ Significa que la migración completó pero vistas viejas aún existen
→ Solución: Ver GUIA_APLICAR_CAMBIOS_SUPABASE.md sección "Problemas"
```

### Error: "Foreign key constraint violated"
```
→ Hay documentos viejos que referencian tematicas borradas
→ Solución: Migración lo maneja automáticamente
→ Si persiste: Ver GUIA_APLICAR_CAMBIOS_SUPABASE.md
```

### El modelo no entrena
```
→ Asegurate que:
  - Python 3.8+
  - scikit-learn instalado (pip install scikit-learn)
  - PDFs de training existen en código
→ Solución: Ver worker/entrenar_modelo.py para detalles
```

### POST /upload falla
```
→ Probables causas:
  1. Modelo no entrenado (ejecuta paso 4)
  2. Workers no están corriendo (startup los 3)
  3. BD no migrada (ejecuta paso 3)
→ Solución: Revisar logs en terminal
```

---

## 📚 DOCUMENTACIÓN COMPLETA

Si necesitas más detalles:

| Pregunta | Archivo |
|----------|---------|
| "¿Qué cambió exactamente?" | COMPARACION_SCHEMA_ANTES_DESPUES.md |
| "¿Cómo ejecuto la migración?" | GUIA_APLICAR_CAMBIOS_SUPABASE.md |
| "¿Cuál es el impacto?" | RESUMEN_CAMBIOS_FINALES.md |
| "¿Qué pasa si falla?" | GUIA_APLICAR_CAMBIOS_SUPABASE.md (sección Rollback) |
| "¿Cuándo hacer cada cosa?" | Este archivo (QUICK_START.md) |

---

## 🎯 RESUMEN

```
ANTES:
Juan crea "Mi IA" → Maria crea "IA" → ML confundido ❌

DESPUÉS:
Catálogo fijo para todos:
├─ Tecnología/Inteligencia Artificial
├─ Tecnología/Redes
├─ Ciencias/Biología
└─ Otros/General

Juan sube PDF → Clasificado automáticamente ✅
Maria sube PDF → Clasificado automáticamente ✅
Ambos ven su catálogo igual → ML consistente ✅
```

---

## 🚀 ¿LISTO PARA COMENZAR?

**Ahora:**
1. Abre: `COMPARACION_SCHEMA_ANTES_DESPUES.md`
2. Lee la sección "ANTES" vs "DESPUÉS"
3. Luego vuelve aquí y sigue los 5 pasos

**Necesitas 40 minutos sin interrupciones.**

**¡Adelante!** 🚀
