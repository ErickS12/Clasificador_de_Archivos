"""
Clasificador
------------
Pipeline TF-IDF + Regresión Logística entrenado con un dataset embebido.
Recibe una lista plana de áreas + subáreas del usuario para validar el resultado.
Si el área predicha no coincide con ninguna del usuario → devuelve "General".
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

TRAINING_DATA = [
    # IA / Machine Learning
    ("neural network deep learning model training accuracy loss", "IA"),
    ("artificial intelligence classification supervised learning", "IA"),
    ("natural language processing transformer bert embeddings", "IA"),
    ("convolutional neural network image recognition feature extraction", "IA"),
    ("reinforcement learning reward policy agent environment", "IA"),
    ("generative model GAN variational autoencoder latent space", "IA"),
    ("gradient boosting random forest decision tree ensemble", "IA"),

    # Redes
    ("network protocol routing topology packet transmission", "Redes"),
    ("wireless sensor network bandwidth latency throughput", "Redes"),
    ("TCP IP socket communication distributed network layer", "Redes"),
    ("network security firewall intrusion detection vulnerability", "Redes"),
    ("5G mobile network antenna signal interference", "Redes"),
    ("software defined networking SDN OpenFlow controller", "Redes"),
    ("peer to peer overlay gossip protocol", "Redes"),

    # Protocolos (subtemática de Redes)
    ("HTTP HTTPS REST protocol request response header", "Protocolos"),
    ("TCP UDP handshake flow control congestion protocol", "Protocolos"),
    ("MQTT CoAP IoT lightweight protocol message broker", "Protocolos"),
    ("BGP OSPF routing protocol autonomous system", "Protocolos"),

    # Topologías (subtemática de Redes)
    ("star mesh ring bus topology network layout", "Topologías"),
    ("tree hybrid topology nodes edges graph network", "Topologías"),

    # Sistemas Operativos
    ("operating system kernel process thread scheduler", "Sistemas Operativos"),
    ("memory management paging segmentation virtual address", "Sistemas Operativos"),
    ("deadlock mutex semaphore synchronization concurrency", "Sistemas Operativos"),
    ("file system inode block directory storage", "Sistemas Operativos"),

    # Sistemas Distribuidos
    ("distributed system consensus fault tolerance replication", "Sistemas Distribuidos"),
    ("CAP theorem consistency availability partition", "Sistemas Distribuidos"),
    ("MapReduce Hadoop Spark distributed computing cluster", "Sistemas Distribuidos"),
    ("microservices container Docker Kubernetes orchestration", "Sistemas Distribuidos"),

    # Bases de Datos
    ("database SQL relational schema normalization query", "Bases de Datos"),
    ("NoSQL MongoDB indexing transaction consistency", "Bases de Datos"),
    ("data warehouse ETL OLAP aggregation reporting", "Bases de Datos"),
    ("distributed database replication sharding partition", "Bases de Datos"),
    ("ACID properties concurrency control locking", "Bases de Datos"),

    # Biología
    ("genomics DNA sequence protein expression cell", "Biología"),
    ("CRISPR gene editing mutation chromosome biology", "Biología"),
    ("bioinformatics phylogenetics evolution species", "Biología"),

    # Matemáticas
    ("theorem proof algebra topology manifold differential", "Matemáticas"),
    ("numerical method optimization convergence", "Matemáticas"),
    ("stochastic process probability distribution variance", "Matemáticas"),
    ("linear algebra matrix eigenvalue decomposition", "Matemáticas"),
]

textos  = [t for t, _ in TRAINING_DATA]
etiquetas = [l for _, l in TRAINING_DATA]

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
    ("clf",   LogisticRegression(max_iter=1000)),
])
pipeline.fit(textos, etiquetas)


def clasificar(texto: str, áreas_usuario: list[str]) -> str:
    """
    Clasifica el texto. Si el área predicha no está en áreas_usuario,
    devuelve 'General'.

    Parámetros:
        texto       — texto extraído del PDF
        áreas_usuario — lista plana de áreas y subáreas del usuario

    Retorna:
        nombre del área predicha o 'General'
    """
    limpio     = texto.lower()[:3000]
    predicho = pipeline.predict([limpio])[0]
    return predicho if predicho in áreas_usuario else "General"
