# 📚 Documentación del API Gateway

## 🎯 Resumen Ejecutivo

El **API Gateway** es la puerta de entrada del sistema distribuido de clasificación de documentos científicos. Su rol es:
1. **Validar** archivos antes de procesarlos
2. **Registrar** todas las operaciones para monitoreo
3. **Coordinar** con el módulo de consenso para distribuir trabajo a workers

---

## 🔍 Componentes del Gateway

### 1. LoggingMiddleware (Monitoreo)

```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Registra cada solicitud con tiempo de ejecución
```

**¿Qué hace?**
- Intercepta TODAS las solicitudes HTTP
- Mide el tiempo que tarda cada request
- Imprime un registro en consola

**Salida esperada:**
```
[GATEWAY] POST /upload → 200 (2.345s)
[GATEWAY] GET /categories → 200 (0.045s)
[GATEWAY] POST /login → 401 (0.023s)
```

**¿Por qué es importante?**
- ✅ **Debugging**: Identifica qué requests son lentos
- ✅ **Auditoría**: Rastrea todas las operaciones
- ✅ **Performance**: Mide tiempo de respuesta de cada endpoint
- ✅ **Monitoreo**: Detecta patrones de error

---

### 2. validar_carga() (Validación)

```python
def validar_carga(archivo: UploadFile):
    """Valida que archivo sea PDF y no supere 10 MB"""
```

**Validaciones que realiza:**

| Validación | Condición | Error |
|---|---|---|
| **Tipo de archivo** | ¿Es `.pdf`? | 400 (Bad Request) |
| **Tamaño máximo** | ¿< 10 MB? | 413 (Payload Too Large) |

**Ejemplo de error:**
```json
{
  "detail": "Solo se aceptan archivos PDF."
}
```

**¿Por qué es importante?**
- ✅ **Seguridad**: Evita cargas malformadas
- ✅ **Recursos**: No procesa archivos enormes
- ✅ **UX**: Da mensajes de error claros al cliente
- ✅ **Integridad**: Garantiza que solo PDFs válidos llegan a workers

---

## 🔗 Integración con el Sistema Completo

### Flujo de una solicitud de upload:

```
1. CLIENTE
   └─ POST /upload (PDF + áreas de interés)
      
2. GATEWAY - LoggingMiddleware
   └─ [GATEWAY] POST /upload → inicio
   
3. GATEWAY - validar_carga()
   ├─ ¿Es .pdf? ✅
   ├─ ¿< 10 MB? ✅
   └─ Validación OK
   
4. MAIN.PY - endpoint /upload
   ├─ Crea metadatos del documento
   ├─ Guarda archivo en storage/nodeX
   └─ Llama a consensus.py
   
5. CONSENSUS.PY
   ├─ Envía PDF a worker 1 (localhost:5001)
   ├─ Envía PDF a worker 2 (localhost:5002)
   └─ Envía PDF a worker 3 (localhost:5003)
   
6. WORKER/MAIN.PY (3 instancias en paralelo)
   ├─ node1: clasificador_1(PDF) → "Machine Learning"
   ├─ node2: clasificador_2(PDF) → "Machine Learning"
   └─ node3: clasificador_3(PDF) → "Data Science"
   
7. CONSENSUS.PY - Votación
   ├─ Votos: [ML, ML, DS]
   ├─ Ganador: "Machine Learning" (2 votos)
   └─ Confianza: 66.7%
   
8. MAIN.PY - Respuesta
   └─ Retorna clasificación + votos
   
9. GATEWAY - LoggingMiddleware
   └─ [GATEWAY] POST /upload → 200 (2.345s)
   
10. CLIENTE
    └─ Recibe JSON con resultado
```

---

## 📊 Herramientas Utilizadas

| Herramienta | Uso | Línea |
|---|---|---|
| **FastAPI** | Framework para endpoints HTTP | `from fastapi import ...` |
| **Starlette** | Base para middleware | `from starlette.middleware.base import ...` |
| **Python `time`** | Medir duración | `import time` |
| **HTTPException** | Respuestas de error | `raise HTTPException(status_code=...)` |

### Stack Técnico Completo:
```
┌─────────────────────────────────────┐
│  FastAPI (Gateway + Endpoints)      │
├─────────────────────────────────────┤
│  Starlette (Middleware, Request)    │
├─────────────────────────────────────┤
│  Uvicorn (Servidor ASGI)            │
├─────────────────────────────────────┤
│  Python asyncio (Programación async)│
└─────────────────────────────────────┘
```

---

## 🎯 Archivos Relacionados

### En `master/`
- **gateway.py** ← Validación + Logging
- **main.py** ← Endpoints principales (usa gateway.py)
- **consensus.py** ← Distribuye a workers
- **auth.py** ← Autenticación
- **adapter.py** ← Transformación de datos

### En `worker/`
- **main.py** ← API del worker
- **classifier.py** ← Modelo ML (TF-IDF + LogisticRegression)
- **extractor.py** ← Extrae texto de PDFs
- **sync.py** ← Sincronización entre nodos

---

## 🚀 Cómo se Inicia

### Terminal 1 - Master (con gateway)
```bash
cd master/
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Output:
```
[GATEWAY] POST /register → 200 (0.012s)
[GATEWAY] POST /login → 200 (0.015s)
```

### Terminal 2-4 - Workers (los que reciben solicitudes del gateway)
```bash
cd worker/
uvicorn main:app --host 0.0.0.0 --port 5001 --reload  # Worker 1
uvicorn main:app --host 0.0.0.0 --port 5002 --reload  # Worker 2
uvicorn main:app --host 0.0.0.0 --port 5003 --reload  # Worker 3
```

---

## 🔐 Flujo de Seguridad

```
Cliente (sin token)
  ↓
validar_carga() ✅ Valida tipo/tamaño
  ↓
auth.py ✅ Verifica token JWT
  ↓
Endpoint protegido
  ↓
LoggingMiddleware ✅ Registra operación
```

---

## 📈 Métricas de Performance

El LoggingMiddleware permite identificar:

```
Rápidos (< 0.1s):
  [GATEWAY] GET /categories → 200 (0.045s)

Normales (0.1s - 3s):
  [GATEWAY] POST /upload → 200 (2.345s)

Lentos (> 3s):
  [GATEWAY] POST /upload → 200 (5.678s) ⚠️
```

Si ves uploads lentos, probablemente:
- Un worker no responde (ve consensus.py)
- El PDF es muy grande
- La red está congestionada

---

## 🛠️ Cómo Modificar

### Cambiar límite de tamaño:
```python
TAM_MAX_ARCHIVOS_MB = 20  # De 10 MB a 20 MB
```

### Agregar nuevo tipo de archivo (ej: .docx):
```python
if not (archivo.filename.lower().endswith(".pdf") or 
        archivo.filename.lower().endswith(".docx")):
    raise HTTPException(...)
```

### Desactivar logging:
```python
# Comentar en main.py:
# app.add_middleware(LoggingMiddleware)
```

---

## ❓ Preguntas Frecuentes

**P: ¿Por qué falla con "Error 413"?**  
R: El archivo supera 10 MB. Convierte el PDF con mejor compresión.

**P: ¿Dónde veo los logs?**  
R: En la terminal donde corriste `uvicorn main:app`. Busca `[GATEWAY]`.

**P: ¿Qué pasa si todos los workers están caídos?**  
R: `consensus.py` lanza error 503. Ver el archivo consensus.py para detalles.

**P: ¿El gateway valida el contenido del PDF?**  
R: No, solo verifica extensión y tamaño. El contenido lo valida `extractor.py` en el worker.

---

## 📝 Resumen

| Componente | Función | Salida |
|---|---|---|
| LoggingMiddleware | Monitorea todas las solicitudes | `[GATEWAY] POST /upload → 200 (2.3s)` |
| validar_carga() | Valida PDF + tamaño | Error 400/413 o continúa |
| Integración | Coordina con consensus.py | Distribuye a 3 workers |

El gateway es **simple pero crítico**: sin él, el sistema aceptaría cualquier archivo y no sabrías qué solicitudes son lentas.
