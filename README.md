# Clasificador Distribuido de Archivos Científicos

## Estado actual

Las Fases 1, 2 y 3 están completamente implementadas y funcionales con JSON.
Ver CRONOGRAMA.md para el detalle de lo que falta.

## Estructura

```
clasificador-distribuido/
├── master/
│   ├── main.py                  ✅ Todos los endpoints
│   ├── auth.py                  ✅ Hash contraseñas + tokens
│   ├── gateway.py               ✅ Validación + logging
│   ├── consensus.py             ✅ Mayoría de votos (⚠️ cambiar IPs en Fase 7)
│   ├── adapter.py               ✅ Formato de respuestas
│   ├── database.py              🔲 Stub Supabase (Fase 4)
│   ├── deletion_coordinator.py  🔲 Stub borrado 2 pasos (Fase 5)
│   └── apa.py                   🔲 Stub generador APA 7 (Fase 8)
├── worker/
│   ├── main.py                  ✅ /process  |  🔲 /delete-files (Fase 5)
│   ├── extractor.py             ✅ Extrae texto PDF
│   ├── classifier.py            ✅ TF-IDF + LogisticRegression
│   └── sync.py                  🔲 Stub Startup Sync (Fase 6)
├── metadata/
│   ├── users.json               ✅ Usuarios y áreas (se migra a Supabase en Fase 4)
│   └── users/                   ✅ JSON por usuario
├── storage/
│   ├── node1/                   ✅ Nodo primario
│   ├── node2/                   ✅ Réplica 1
│   └── node3/                   ✅ Réplica 2
├── frontend/
│   └── README_FRONTEND.md       🔲 Guía de implementación React (Fase 8)
├── .env.example                 ← copiar como .env al migrar a Supabase
├── requirements.txt
└── CRONOGRAMA.md
```

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución (Fases 1-3, todo en localhost)

Abrir 4 terminales desde la raíz del proyecto:

```bash
# Terminal 1
uvicorn worker.main:app --port 5001

# Terminal 2
uvicorn worker.main:app --port 5002

# Terminal 3
uvicorn worker.main:app --port 5003

# Terminal 4
uvicorn master.main:app --port 8000
```

Documentación interactiva: http://localhost:8000/docs

## Ejecución en LAN (Fase 7 — pendiente)

```bash
# En cada laptop worker, cambiar localhost por 0.0.0.0
uvicorn worker.main:app --host 0.0.0.0 --port 5001

# Actualizar IPs en master/consensus.py
WORKERS = [
    "http://192.168.x.x:5001/process",
    "http://192.168.x.x:5002/process",
    "http://192.168.x.x:5003/process",
]
```

## Flujo de uso básico

```
1. POST /register?username=erick&password=mipass
   → primer usuario = admin automático

2. POST /login?username=erick&password=mipass
   → { "token": "uuid..." }

3. Usar token en header de todos los demás requests:
   Authorization: Bearer uuid...

4. POST /areas?area=Redes
5. POST /areas/Redes/sub?subarea=Protocolos
6. POST /upload  (form-data: file=paper.pdf)
7. GET  /files
8. GET  /download?filename=paper.pdf&area=Redes&subarea=Protocolos
9. DELETE /document?filename=paper.pdf&area=Redes&subarea=Protocolos
```
