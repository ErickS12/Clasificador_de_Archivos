# Diagramas Visuales

Diagramas de arquitectura y secuencia del sistema distribuido.

## 1. Arquitectura general

```text
Cliente
  |
  v
Nodo líder (master)
  |- auth
  |- gateway
  |- consensus
  |- routes
  |
  +----> Nodo 1 (/process)
  +----> Nodo 2 (/process)
  +----> Nodo 3 (/process)

Servicios compartidos
  |- shared/election.py
  |- shared/leader_db.py

Persistencia
  |- Supabase (usuarios, tokens_sesion, tematicas, subtematicas)
  |- Supabase (documentos, nodos_almacenamiento, consenso_votos)
  |- storage/node1-node3
```

## 2. Secuencia de clasificacion

```text
Cliente -> Líder: POST /upload
Líder -> Gateway: validar_carga
Líder -> Nodo1: /process
Líder -> Nodo2: /process
Líder -> Nodo3: /process
Nodos -> Líder: area predicha
Líder -> Consensus: mayoria
Líder -> Supabase/Storage: guardar
Líder -> Cliente: respuesta final
```

## 3. Secuencia de liderazgo

```text
Nodo A -> Lider: heartbeat
Nodo B -> Lider: heartbeat
Lider cae
Nodo A -> cluster: election/start
Nodo con mayor ID disponible: gana
Ganador -> leader_db: actualizar lider
Nodos -> nuevo lider: redireccion de trafico
```

## 4. Flujo de descarga

```text
Cliente -> Líder: GET /download
Líder -> node1: buscar archivo
si no existe -> node2
si no existe -> node3
si existe -> FileResponse
si no existe en ninguno -> 404
```

## 5. Mapa de componentes

```text
master/
  main.py
  routes.py
  auth.py
  gateway.py
  consensus.py
  adapter.py

worker/
  main.py
  extractor.py
  classifier.py

shared/
  election.py
  leader_db.py
```

## 6. Operacion recomendada

```text
1) Iniciar nodos
2) Iniciar líder
3) Verificar /leader y /docs
4) Ejecutar pruebas de upload/download
5) Simular caida de lider para validar failover
```

