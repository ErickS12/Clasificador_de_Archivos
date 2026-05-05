# ðŸš€ GUÃA RÃPIDA: Los 5 Pasos Finales

**Tiempo total: ~40 minutos**

---

## â±ï¸ PASO 1: LEE (5 MIN)

Lee este archivo primero para entender quÃ© va a pasar:

```
ðŸ“„ COMPARACION_SCHEMA_ANTES_DESPUES.md
   â†“
   EntenderÃ¡s quÃ© cambia en la BD
```

---

## ðŸ’¾ PASO 2: BACKUP (5 MIN)

**MÃS IMPORTANTE ANTES DE TOCAR LA BD**

### OpciÃ³n A: Supabase Dashboard (Recomendado)
```
1. Ve a: https://app.supabase.com
2. Selecciona tu proyecto
3. Settings â†’ Backups â†’ Create backup
4. Espera a que se complete
```

### OpciÃ³n B: Exportar datos (Como respaldo adicional)
```
1. Ve a SQL Editor en Supabase
2. Ejecuta:
   SELECT * FROM tematicas;
   SELECT * FROM subtematicas;
   SELECT * FROM documentos;
3. Descarga como CSV
```

---

## ðŸ—„ï¸ PASO 3: MIGRACIÃ“N SQL (2 MIN)

**Ejecutar en Supabase:**

```
1. Abre: https://app.supabase.com/project/[TU-PROYECTO]/sql/new
2. Abre el archivo: MIGRACION_CATALOGO_GLOBAL.sql (en tu carpeta)
3. Copia TODO el contenido
4. PÃ©galo en Supabase SQL Editor
5. Presiona: "Run" (botÃ³n azul)
6. Espera a que complete (toma ~30 segundos)
```

**DeberÃ­a ver algo como:**
```
âœ… CREATE TABLE
âœ… INSERT 3 rows into tematicas
âœ… INSERT 8 rows into subtematicas
âœ… DROP TRIGGER
âœ… CREATE VIEW
âœ… SELECT (resultados de verificaciÃ³n)
```

---

## ðŸ¤– PASO 4: ENTRENAR MODELO (5-10 MIN)

**En tu terminal local:**

```bash
cd c:\Clasificador_de_Archivos
python worker/entrenar_modelo.py
```

**DeberÃ­a ver:**
```
Loading training data...
Training model (hierarchical labels)...
TF-IDF Vectorizer trained with 6 categories
LogisticRegression trained with 6 labels
Model saved to: worker/modelo_clasificador.pkl
Training complete!
```

---

## âœ… PASO 5: VERIFICAR (10 MIN)

### 5.1: Verificar estructura en Supabase
```sql
-- Copiar y ejecutar en Supabase SQL Editor

-- Ver tematicas globales
SELECT id, nombre FROM tematicas;
-- Esperado: 3 filas (TecnologÃ­a, Ciencias, Otros)

-- Ver subtematicas
SELECT t.nombre AS tematica, s.nombre AS subtematica
FROM subtematicas s
JOIN tematicas t ON t.id = s.tematica_id
ORDER BY t.nombre, s.nombre;
-- Esperado: 8 filas

-- Verificar que NO hay usuario_id
SELECT column_name FROM information_schema.columns
WHERE table_name = 'tematicas';
-- NO debe aparecer usuario_id âœ“
```

### 5.2: Probar API (desde terminal)

```bash
# Verificar que servidor estÃ¡ corriendo
# Terminal 1:
cd c:\Clasificador_de_Archivos
python master/main.py

# Terminal 2:
cd c:\Clasificador_de_Archivos
python worker/main.py

# Terminal 3: Pruebas
# Prueba 1: Ver catÃ¡logo global
curl -X GET http://localhost:8000/categories

# Esperado:
# {
#   "categorias_globales": [
#     "TecnologÃ­a/Inteligencia Artificial",
#     "TecnologÃ­a/Redes",
#     "TecnologÃ­a/Bases de Datos",
#     "TecnologÃ­a/Sistemas Operativos",
#     "TecnologÃ­a/Sistemas Distribuidos",
#     "Ciencias/BiologÃ­a",
#     "Ciencias/MatemÃ¡ticas",
#     "Otros/General"
#   ]
# }

# Prueba 2: Subir PDF
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer test-token" \
  -F "archivo=@test.pdf"

# DeberÃ­a clasificar automÃ¡ticamente con consenso de 3 workers
```

---

## âœ… CHECKLIST POST-MIGRACIÃ“N

```
DespuÃ©s de completar los 5 pasos, verificar:

Base de Datos:
  â˜ Tabla tematicas tiene 3 registros (sin usuario_id)
  â˜ Tabla subtematicas tiene 8 registros
  â˜ Vista vista_arbol_usuario funciona sin errores
  â˜ NO hay columna usuario_id en tematicas

Modelo:
  â˜ Archivo worker/modelo_clasificador.pkl fue creado
  â˜ Size > 1KB (no estÃ¡ vacÃ­o)

API:
  â˜ GET /categories devuelve 8 categorÃ­as globales
  â˜ POST /upload clasifica automÃ¡ticamente
  â˜ Logs muestran: "3/3 workers agree" (consenso)
  â˜ No hay errores de "foreign key" en logs

Testing:
  â˜ ProbÃ© con 1+ PDF
  â˜ SubÃ­ archivo con usuario autenticado
  â˜ DescarguÃ© archivo subido
  â˜ ClasificaciÃ³n fue automÃ¡tica
```

---

## ðŸ†˜ SI ALGO SALE MAL

### Error: "Column usuario_id does not exist"
```
â†’ Significa que la migraciÃ³n completÃ³ pero vistas viejas aÃºn existen
â†’ SoluciÃ³n: Ver GUIA_APLICAR_CAMBIOS_SUPABASE.md secciÃ³n "Problemas"
```

### Error: "Foreign key constraint violated"
```
â†’ Hay documentos viejos que referencian tematicas borradas
â†’ SoluciÃ³n: MigraciÃ³n lo maneja automÃ¡ticamente
â†’ Si persiste: Ver GUIA_APLICAR_CAMBIOS_SUPABASE.md
```

### El modelo no entrena
```
â†’ Asegurate que:
  - Python 3.8+
  - scikit-learn instalado (pip install scikit-learn)
  - PDFs de training existen en cÃ³digo
â†’ SoluciÃ³n: Ver worker/entrenar_modelo.py para detalles
```

### POST /upload falla
```
â†’ Probables causas:
  1. Modelo no entrenado (ejecuta paso 4)
  2. Workers no estÃ¡n corriendo (startup los 3)
  3. BD no migrada (ejecuta paso 3)
â†’ SoluciÃ³n: Revisar logs en terminal
```

---

## ðŸ“š DOCUMENTACIÃ“N COMPLETA

Si necesitas mÃ¡s detalles:

| Pregunta | Archivo |
|----------|---------|
| "Â¿QuÃ© cambiÃ³ exactamente?" | COMPARACION_SCHEMA_ANTES_DESPUES.md |
| "Â¿CÃ³mo ejecuto la migraciÃ³n?" | GUIA_APLICAR_CAMBIOS_SUPABASE.md |
| "Â¿CuÃ¡l es el impacto?" | RESUMEN_CAMBIOS_FINALES.md |
| "Â¿QuÃ© pasa si falla?" | GUIA_APLICAR_CAMBIOS_SUPABASE.md (secciÃ³n Rollback) |
| "Â¿CuÃ¡ndo hacer cada cosa?" | Este archivo (QUICK_START.md) |

---

## ðŸŽ¯ RESUMEN

```
ANTES:
Juan crea "Mi IA" â†’ Maria crea "IA" â†’ ML confundido âŒ

DESPUÃ‰S:
CatÃ¡logo fijo para todos:
â”œâ”€ TecnologÃ­a/Inteligencia Artificial
â”œâ”€ TecnologÃ­a/Redes
â”œâ”€ Ciencias/BiologÃ­a
â””â”€ Otros/General

Juan sube PDF â†’ Clasificado automÃ¡ticamente âœ…
Maria sube PDF â†’ Clasificado automÃ¡ticamente âœ…
Ambos ven su catÃ¡logo igual â†’ ML consistente âœ…
```

---

## ðŸš€ Â¿LISTO PARA COMENZAR?

**Ahora:**
1. Abre: `COMPARACION_SCHEMA_ANTES_DESPUES.md`
2. Lee la secciÃ³n "ANTES" vs "DESPUÃ‰S"
3. Luego vuelve aquÃ­ y sigue los 5 pasos

**Necesitas 40 minutos sin interrupciones.**

**Â¡Adelante!** ðŸš€

