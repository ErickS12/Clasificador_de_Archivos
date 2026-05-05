# Worker â€” Nodo de Procesamiento

Nodo encargado de procesar PDFs: extracciÃ³n de texto y clasificaciÃ³n automÃ¡tica.

## Estructura

- `main.py` â€” Servidor FastAPI que expone endpoints de procesamiento
- `extractor.py` â€” ExtracciÃ³n de texto desde PDFs (PyMuPDF)
- `classifier.py` â€” ClasificaciÃ³n TF-IDF + LogisticRegression con persistencia de modelo
- `sync.py` â€” (Pendiente Fase 6) SincronizaciÃ³n de datos al iniciar
- `entrenar_modelo.py` â€” Script para entrenar/reentrenar el modelo manualmente

## Persistencia del Modelo de ClasificaciÃ³n

### CÃ³mo funciona

El modelo de clasificaciÃ³n se entrena una sola vez y se guarda en disco:

1. **Primer inicio**: El worker entrena el modelo (`_entrenar_modelo()`) y lo guarda en `modelo_clasificador.pkl`
2. **Inicios posteriores**: El worker carga el modelo desde disco (`_cargar_modelo()`), tardando milisegundos

### UbicaciÃ³n del Modelo

```
worker/modelo_clasificador.pkl
```

Este archivo NO se versiona en git (ver `.gitignore`).

### Reentrenamiento Manual

Si necesitas entrenar el modelo desde cero (por ejemplo, despuÃ©s de actualizar `TRAINING_DATA`):

```bash
python worker/entrenar_modelo.py
```

El script pedirÃ¡ confirmaciÃ³n si el modelo ya existe.

## Endpoints

### POST /process

Clasifica un PDF.

**Request:**
```
Content-Type: multipart/form-data
- archivo: File (PDF)
- areas_usuario: JSON string con Ã¡reas permitidas

Ejemplo:
{
  "areas_usuario": ["Redes", "Protocolos", "TopologÃ­as", "General"]
}
```

**Response:**
```json
{
  "area": "Redes"
}
```

### GET /heartbeat

Responde para confirmar que el nodo estÃ¡ vivo (parte del protocolo de elecciÃ³n de lÃ­der).

**Response:**
```json
{
  "nodo_id": 1,
  "lider": false
}
```

## Variables de Entorno

- `NODO_ID`: ID Ãºnico del nodo (1-4). Usado en elecciÃ³n de lÃ­der. Default: varÃ­a segÃºn worker
- `ALMACENAMIENTO_NODO`: Ruta donde almacenar rÃ©plicas de documentos. Default: `../storage/node1`

### Ejemplo de EjecuciÃ³n

```bash
# Worker 1 (nodo 1)
export NODO_ID=1
export ALMACENAMIENTO_NODO=../storage/node1
uvicorn main:app --port 5001

# Worker 2 (nodo 2)
export NODO_ID=2
export ALMACENAMIENTO_NODO=../storage/node2
uvicorn main:app --port 5002

# Worker 3 (nodo 3)
export NODO_ID=3
export ALMACENAMIENTO_NODO=../storage/node3
uvicorn main:app --port 5003
```

## Dependencias

Ver `requirements.txt` en la raÃ­z del proyecto.

Principales:
- `scikit-learn` â€” Modelos ML y TF-IDF
- `PyMuPDF` â€” ExtracciÃ³n de texto de PDFs
- `joblib` â€” SerializaciÃ³n de modelos (incluido en scikit-learn)
- `FastAPI` â€” API REST
- `requests` â€” ComunicaciÃ³n con master

## IntegraciÃ³n con Cluster

El worker se integra con el sistema de elecciÃ³n de lÃ­der (`shared/election.py`):

1. Al iniciar, se registra en el clÃºster
2. Participa en heartbeat del lÃ­der
3. Si el lÃ­der cae, participa en la elecciÃ³n (algoritmo Bully)
4. Si gana la elecciÃ³n, activa las rutas del maestro (`master/routes.py`)

Ver `shared/election.py` para detalles del protocolo de elecciÃ³n.

