"""
Clasificador
------------
Pipeline TF-IDF + Regresión Logística entrenado con un dataset embebido.
El modelo se guarda en disco para evitar reentrenamiento en cada inicio.

Recibe una lista plana de áreas y subáreas del usuario para validar el resultado.
Si el área predicha no coincide con ninguna del usuario devuelve "General".
"""

import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Ruta donde se guardará el modelo entrenado
MODELO_RUTA = os.path.join(os.path.dirname(__file__), "modelo_clasificador.pkl")

TRAINING_DATA = [
    # Tecnología / Inteligencia Artificial
    ("neural network deep learning model training accuracy loss", "Tecnología/Inteligencia Artificial"),
    ("artificial intelligence classification supervised learning", "Tecnología/Inteligencia Artificial"),
    ("natural language processing transformer bert embeddings", "Tecnología/Inteligencia Artificial"),
    ("convolutional neural network image recognition feature extraction", "Tecnología/Inteligencia Artificial"),
    ("reinforcement learning reward policy agent environment", "Tecnología/Inteligencia Artificial"),
    ("generative model GAN variational autoencoder latent space", "Tecnología/Inteligencia Artificial"),
    ("gradient boosting random forest decision tree ensemble", "Tecnología/Inteligencia Artificial"),
    ("machine learning classification regression clustering", "Tecnología/Inteligencia Artificial"),
    ("neural network training optimization backpropagation", "Tecnología/Inteligencia Artificial"),

    # Tecnología / Redes
    ("network protocol routing topology packet transmission", "Tecnología/Redes"),
    ("wireless sensor network bandwidth latency throughput", "Tecnología/Redes"),
    ("TCP IP socket communication distributed network layer", "Tecnología/Redes"),
    ("network security firewall intrusion detection vulnerability", "Tecnología/Redes"),
    ("5G mobile network antenna signal interference", "Tecnología/Redes"),
    ("software defined networking SDN OpenFlow controller", "Tecnología/Redes"),
    ("peer to peer overlay gossip protocol", "Tecnología/Redes"),
    ("HTTP HTTPS REST protocol request response header", "Tecnología/Redes"),
    ("TCP UDP handshake flow control congestion protocol", "Tecnología/Redes"),
    ("MQTT CoAP IoT lightweight protocol message broker", "Tecnología/Redes"),
    ("BGP OSPF routing protocol autonomous system", "Tecnología/Redes"),
    ("star mesh ring bus topology network layout", "Tecnología/Redes"),
    ("tree hybrid topology nodes edges graph network", "Tecnología/Redes"),

    # Tecnología / Bases de Datos
    ("database SQL relational schema normalization query", "Tecnología/Bases de Datos"),
    ("NoSQL MongoDB indexing transaction consistency", "Tecnología/Bases de Datos"),
    ("data warehouse ETL OLAP aggregation reporting", "Tecnología/Bases de Datos"),
    ("distributed database replication sharding partition", "Tecnología/Bases de Datos"),
    ("ACID properties concurrency control locking", "Tecnología/Bases de Datos"),
    ("database index optimization query execution plan", "Tecnología/Bases de Datos"),

    # Ciencias / Biología
    ("genomics DNA sequence protein expression cell", "Ciencias/Biología"),
    ("CRISPR gene editing mutation chromosome biology", "Ciencias/Biología"),
    ("bioinformatics phylogenetics evolution species", "Ciencias/Biología"),
    ("molecular biology enzyme reaction metabolic pathway", "Ciencias/Biología"),
    ("organism ecosystem habitat natural selection", "Ciencias/Biología"),

    # Ciencias / Matemáticas
    ("theorem proof algebra topology manifold differential", "Ciencias/Matemáticas"),
    ("numerical method optimization convergence", "Ciencias/Matemáticas"),
    ("stochastic process probability distribution variance", "Ciencias/Matemáticas"),
    ("linear algebra matrix eigenvalue decomposition", "Ciencias/Matemáticas"),
    ("calculus integral derivative limit function", "Ciencias/Matemáticas"),
    ("geometry coordinate transformation vector space", "Ciencias/Matemáticas"),

    # Sistemas Operativos (subcategoría de Tecnología)
    ("operating system kernel process thread scheduler", "Tecnología/Sistemas Operativos"),
    ("memory management paging segmentation virtual address", "Tecnología/Sistemas Operativos"),
    ("deadlock mutex semaphore synchronization concurrency", "Tecnología/Sistemas Operativos"),
    ("file system inode block directory storage", "Tecnología/Sistemas Operativos"),

    # Sistemas Distribuidos (subcategoría de Tecnología)
    ("distributed system consensus fault tolerance replication", "Tecnología/Sistemas Distribuidos"),
    ("CAP theorem consistency availability partition", "Tecnología/Sistemas Distribuidos"),
    ("MapReduce Hadoop Spark distributed computing cluster", "Tecnología/Sistemas Distribuidos"),
    ("microservices container Docker Kubernetes orchestration", "Tecnología/Sistemas Distribuidos"),
]


def _entrenar_modelo() -> Pipeline:
    """Entrena el modelo y lo guarda en disco."""
    print("[CLASSIFIER] Entrenando modelo... esto puede tomar unos segundos.")
    textos    = [t for t, _ in TRAINING_DATA]
    etiquetas = [l for _, l in TRAINING_DATA]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf",   LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(textos, etiquetas)
    
    # Guardar el modelo en disco
    joblib.dump(pipeline, MODELO_RUTA)
    print(f"[CLASSIFIER] Modelo guardado en {MODELO_RUTA}")
    return pipeline


def _cargar_modelo() -> Pipeline:
    """Carga el modelo desde disco. Si no existe, lo entrena primero."""
    if os.path.exists(MODELO_RUTA):
        print(f"[CLASSIFIER] Cargando modelo desde {MODELO_RUTA}")
        pipeline = joblib.load(MODELO_RUTA)
    else:
        pipeline = _entrenar_modelo()
    return pipeline


# Cargar el modelo al importar el módulo
pipeline = _cargar_modelo()


def clasificar(texto: str, categorias_global: list[str]) -> str:
    """
    Clasifica el texto usando el modelo jerárquico.
    
    El modelo predice rutas completas (ej: "Tecnología/Inteligencia Artificial").
    Si la predicción no existe en el catálogo global, devuelve "Otros/General".

    Parámetros:
        texto - texto extraído del PDF
        categorias_global - lista de todas las rutas jerárquicas disponibles
                           (ej: ["Tecnología/IA", "Tecnología/Redes", ...])

    Retorna:
        Ruta jerárquica predicha (ej: "Tecnología/Inteligencia Artificial")
        o "Otros/General" si no encuentra coincidencia
    """
    limpio = texto.lower()[:3000]
    predicho = pipeline.predict([limpio])[0]
    
    # Si la predicción existe en el catálogo, devolverla
    # Si no, devolver fallback a "Otros/General"
    if predicho in categorias_global:
        return predicho
    else:
        return "Otros/General"
