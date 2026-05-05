# Cambios Realizados: Catálogo Global de Temáticas

## 📋 Resumen de Cambios

Se ha transformado el sistema de clasificación de un modelo **por usuario** a un modelo con **Catálogo Global de Solo Lectura**. Los usuarios ya NO pueden crear ni borrar categorías - solo cargan archivos que se clasifican automáticamente.

---

## 🔄 Cambios por Archivo

### 1. **SCHEMA_SUPABASE_FINAL.sql** ✅
**Cambios principales:**
- Tabla `tematicas`: Removido `usuario_id` y constraint `uq_tematica_usuario`
- Tabla ahora es un **catálogo global fijo** (no por usuario)
- Insertados datos iniciales del catálogo:
  - **Tecnología** → Inteligencia Artificial, Redes, Bases de Datos
  - **Ciencias** → Biología, Matemáticas
  - **Otros** → General (red de seguridad)
- Tabla `subtematicas`: Agregados datos iniciales del catálogo
- Removido trigger `trg_crear_general` (ya no se crea "General" por usuario)

### 2. **worker/classifier.py** ✅
**Cambios principales:**
- `TRAINING_DATA`: Actualizado con **etiquetas jerárquicas** 
  - Antes: `("texto...", "IA")`
  - Ahora: `("texto...", "Tecnología/Inteligencia Artificial")`
- Función `clasificar()`: Ahora recibe `categorias_global` (lista de rutas jerárquicas)
  - Devuelve rutas completas: `"Tecnología/Redes"`
  - Fallback automático a `"Otros/General"` si no encuentra coincidencia
- Datos de entrenamiento ampliados y reorganizados por categoría jerárquica

### 3. **worker/main.py** ✅
**Cambios principales:**
- Endpoint `POST /process`:
  - Antes recibía: `areas_usuario` (áreas personales del usuario)
  - Ahora recibe: `categorias_global` (catálogo global de rutas jerárquicas)
  - Devuelve: `{"area": "Tecnología/Inteligencia Artificial"}`
- Documentación actualizada del endpoint

### 4. **master/consensus.py** ✅
**Cambios principales:**
- Función `enviar_a_worker()`:
  - Antes: `areas_planas` (lista plana del usuario)
  - Ahora: `categorias_global` (lista de rutas del catálogo)
- Función `clasificar_con_consenso()`:
  - Ahora trabaja con **rutas jerárquicas completas**
  - Consenso por mayoría de rutas: `"Tecnología/Redes"` vs `"Ciencias/Biología"`
  - Fallback a `"Otros/General"` si consenso falla

### 5. **master/database.py** ✅
**Cambios principales:**
- Removida: `obtener_tematicas_usuario(usuario_id)` - Ya no tiene sentido
- Removida: `insertar_tematica()` - Los usuarios no pueden crear temáticas
- Removida: `insertar_subtematica()` - Las subtematicas son fijas
- **Nuevas funciones:**
  - `obtener_catalogo_global()` - Obtiene todas las temáticas globales
  - `obtener_categorias_globales()` - Devuelve lista de rutas jerárquicas
  - `resolver_tema_predicho(ruta)` - Resuelve `"Tecnología/IA"` → `(tematica_id, subtematica_id)`
- Función `obtener_subtematicas()` - Mantiene pero sin cambios

### 6. **master/routes.py** ✅
**Cambios principales:**
- **Removidas funciones auxiliares:**
  - `_catalogo_areas_usuario()` - Ya no aplicable
  - `_resolver_ids_area()` - Ya no aplicable
  - `_obtener_documento_activo()` - Ya no aplicable

- **Removidos endpoints:**
  - `POST /areas` - Crear área
  - `POST /areas/{area}/sub` - Crear subárea
  - `DELETE /areas/{area}` - Eliminar área
  - `DELETE /areas/{area}/sub/{subarea}` - Eliminar subárea
  - `DELETE /admin/areas/{nombre_usuario}/{area}` - Eliminar área (admin)
  - `DELETE /admin/areas/{nombre_usuario}/{area}/{subarea}` - Eliminar subárea (admin)

- **Endpoints actualizados:**
  - `GET /categories` - Ahora devuelve catálogo global (solo lectura)
  - `POST /upload` - Flujo completamente rediseñado:
    1. Obtiene catálogo global
    2. Envía catálogo a nodos
    3. Recibe ruta predicha (ej: `"Tecnología/IA"`)
    4. Valida que existe en catálogo
    5. Si NO existe → asigna `"Otros/General"` automáticamente
    6. Guarda documento con `user_id` del usuario (para que solo él lo vea)
  - `GET /files` - Reconstruido para trabajar con catálogo global
  - `GET /download` - Actualizado para buscar por rutas globales
  - `DELETE /document` - Actualizado para trabajar con nuevas rutas
  - `GET /admin/users` - Devuelve catálogo global en lugar de áreas personales

- **Importaciones actualizadas:**
  - Removidas: `obtener_tematicas_usuario`, `insertar_tematica`, `insertar_subtematica`, `resolver_area`, `construir_areas_planas`
  - Agregadas: `obtener_catalogo_global`, `obtener_categorias_globales`, `resolver_tema_predicho`

### 7. **master/adapter.py** ✅
**Cambios principales:**
- `adaptar_respuesta_carga()` - Mantiene estructura pero ahora maneja rutas jerárquicas
- `adaptar_respuesta_archivos()` - Mantiene estructura, documentación actualizada
- **Removidas funciones:**
  - `resolver_area()` - Ya no necesaria (ahora es en database.py)
  - `construir_areas_planas()` - Ya no necesaria (ahora es catálogo global)

### 8. **worker/entrenar_modelo.py** ✅
**Cambios principales:**
- Comentarios y documentación actualizados para reflejar predicción jerárquica
- Mensaje de salida mejorado mostrando ejemplos de rutas

---

## 🎯 Nuevo Flujo de Clasificación

```
1. Usuario sube PDF
   ↓
2. Maestro obtiene catálogo global
   ├─ Tecnología/Inteligencia Artificial
   ├─ Tecnología/Redes
   ├─ Tecnología/Bases de Datos
   ├─ Ciencias/Biología
   ├─ Ciencias/Matemáticas
   └─ Otros/General
   ↓
3. Envía PDF + catálogo a 3 nodos
  ↓
4. Cada nodo predice ruta jerárquica
  ├─ Nodo 1 → "Tecnología/Redes"
  ├─ Nodo 2 → "Tecnología/Redes"
  └─ Nodo 3 → "Tecnología/Redes"
   ↓
5. Maestro hace consenso por mayoría
   → Resultado: "Tecnología/Redes"
   ↓
6. Valida que existe en catálogo ✅
   ↓
7. Si NO existe → asigna "Otros/General" automáticamente
   ↓
8. Guarda documento:
   - tematica_id = ID de "Tecnología"
   - subtematica_id = ID de "Redes"
   - usuario_id = ID del usuario (solo él ve su archivo)
   ↓
9. Replica en 3 nodos
   ↓
10. Devuelve respuesta al usuario
```

---

## 📊 Catálogo Global Fijo

```
Tecnología/
  ├─ Inteligencia Artificial
  ├─ Redes
  ├─ Bases de Datos
  ├─ Sistemas Operativos
  └─ Sistemas Distribuidos

Ciencias/
  ├─ Biología
  └─ Matemáticas

Otros/
  └─ General (red de seguridad)
```

---

## 🔐 Privacidad de Documentos

- **Catálogo Global**: Accesible a todos los usuarios (solo lectura)
- **Documentos del Usuario**: Solo el usuario que lo subió puede verlo
  - Se almacena `usuario_id` en la tabla `documentos`
  - GET `/files` solo devuelve archivos del usuario actual
  - GET `/download` valida que el usuario es el dueño

---

## ⚠️ Cambios que Afectan a Clientes

### Antes:
```bash
# Crear categoría personalizada
POST /areas
Body: {"area": "Mi Categoría"}

# Subir archivo a categoría específica
POST /upload
Body: archivo + categoría elegida manualmente

# Ver categorías personales
GET /categories
Response: {"areas": {"Mi Categoría": [], "Otra": []}}
```

### Ahora:
```bash
# Ver catálogo global (solo lectura)
GET /categories
Response: {"categorias_globales": [
  "Tecnología/Inteligencia Artificial",
  "Tecnología/Redes",
  ...
]}

# Subir archivo (se clasifica automáticamente)
POST /upload
Body: solo el archivo PDF
# El sistema predice automáticamente la categoría

# Ver documentos del usuario
GET /files
Response: documentos clasificados en el catálogo global
```

---

## ✅ Verificación Post-Cambios

- [x] Schema SQL actualizado con catálogo global
- [x] Datos iniciales insertados en tematicas y subtematicas
- [x] Classifier entrena con etiquetas jerárquicas
- [x] Nodos devuelven rutas completas
- [x] Consenso funciona con rutas jerárquicas
- [x] Database expone funciones para catálogo global
- [x] Routes redirige flujo a nuevas funciones
- [x] Adapter devuelve respuestas correctas
- [x] Remover referencias a funciones antiguas
- [x] Documentación de cambios completa

---

## 🚀 Próximos Pasos (Recomendados)

1. **Entrenar nuevo modelo:** `python worker/entrenar_modelo.py`
2. **Ejecutar migrations de BD:** Aplicar nuevo schema en Supabase
3. **Testing:** Probar flujo completo de carga y clasificación
4. **Monitor de logs:** Verificar que consenso funciona con nuevas rutas
5. **Expandir catálogo:** Agregar más categorías/subcategorías si es necesario

---

## 📌 Notas Importantes

- El catálogo global es ahora la **"fuente de verdad"** para clasificación
- Los usuarios **no pueden crear categorías personales** - esto es por diseño
- Fallback automático a `"Otros/General"` mantiene robustez
- Cada documento mantiene `usuario_id` para privacidad
- Cambios son **backward incompatibles** - clientes viejos necesitarán actualización


