# Worker — Nodo de Procesamiento

Nodo encargado de procesar PDFs: extracción de texto y clasificación automática.

## Estructura

- `main.py` — Servidor FastAPI que expone endpoints de procesamiento
- `extractor.py` — Extracción de texto desde PDFs (PyMuPDF)
- `classifier.py` — Clasificación TF-IDF + LogisticRegression con persistencia de modelo
- `sync.py` — (Pendiente Fase 6) Sincronización de datos al iniciar
- `entrenar_modelo.py` — Script para entrenar/reentrenar el modelo manualmente

## Persistencia del Modelo de Clasificación

### Cómo funciona

El modelo de clasificación se entrena una sola vez y se guarda en disco:

1. **Primer inicio**: El worker entrena el modelo (`_entrenar_modelo()`) y lo guarda en `modelo_clasificador.pkl`
2. **Inicios posteriores**: El worker carga el modelo desde disco (`_cargar_modelo()`), tardando milisegundos

### Ubicación del Modelo

```
worker/modelo_clasificador.pkl
```

Este archivo NO se versiona en git (ver `.gitignore`).

### Reentrenamiento Manual

Si necesitas entrenar el modelo desde cero (por ejemplo, después de actualizar `TRAINING_DATA`):

```bash
python worker/entrenar_modelo.py
```

El script pedirá confirmación si el modelo ya existe.

## Endpoints

### POST /process

Clasifica un PDF.

**Request:**
```
Content-Type: multipart/form-data
- archivo: File (PDF)
- areas_usuario: JSON string con áreas permitidas

Ejemplo:
{
  "areas_usuario": ["Redes", "Protocolos", "Topologías", "General"]
}
```

**Response:**
```json
{
  "area": "Redes"
}
```

### GET /heartbeat

Responde para confirmar que el nodo está vivo (parte del protocolo de elección de líder).

**Response:**
```json
{
  "nodo_id": 1,
  "lider": false
}
```

## Variables de Entorno

- `NODO_ID`: ID único del nodo (1-4). Usado en elección de líder. Default: varía según worker
- `ALMACENAMIENTO_NODO`: Ruta donde almacenar réplicas de documentos. Default: `../storage/node1`

### Ejemplo de Ejecución

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

Ver `requirements.txt` en la raíz del proyecto.

Principales:
- `scikit-learn` — Modelos ML y TF-IDF
- `PyMuPDF` — Extracción de texto de PDFs
- `joblib` — Serialización de modelos (incluido en scikit-learn)
- `FastAPI` — API REST
- `requests` — Comunicación con master

## Integración con Cluster

El worker se integra con el sistema de elección de líder (`shared/election.py`):

1. Al iniciar, se registra en el clúster
2. Participa en heartbeat del líder
3. Si el líder cae, participa en la elección (algoritmo Bully)
4. Si gana la elección, activa las rutas del maestro (`master/routes.py`)

Ver `shared/election.py` para detalles del protocolo de elección.


