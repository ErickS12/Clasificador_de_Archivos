# Mapa de IntegraciÃ³n - Clasificador Final

## Vista General: Archivos y Conexiones

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                       SUPABASE (Nube)                           â”‚
â”‚  PostgreSQL con 9 tablas, 2 triggers, 4 vistas, Ã­ndices        â”‚
â”‚  (roles, usuarios, tokens, tematicas, subtematicas,            â”‚
â”‚   documentos, nodos_almacenamiento, consenso_votos, lider)     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                               â”‚
                 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                 â”‚                           â”‚
       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
       â”‚  MASTER            â”‚      â”‚  WORKERS          â”‚
       â”‚  (Orquestador)     â”‚      â”‚  (ClasificaciÃ³n)  â”‚
       â”‚                    â”‚      â”‚                   â”‚
       â”‚ main.py            â”‚      â”‚ main.py (x3)      â”‚
       â”‚ routes.py â—„â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”¼â”€ classifier.py    â”‚
       â”‚ gateway.py         â”‚      â”‚ sync.py           â”‚
       â”‚ auth.py            â”‚      â”‚                   â”‚
       â”‚ consensus.py       â”‚      â”‚ localhost:5001    â”‚
       â”‚ adapter.py         â”‚      â”‚ localhost:5002    â”‚
       â”‚ database.py â”€â”€â”€â”€â”€â”€â”â”‚      â”‚ localhost:5003    â”‚
       â”‚                  â”‚â””â”€â”€â”€â”€â”€â”€â–º                   â”‚
       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚                        â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  Archivos Python    â”‚   â”‚  Almacenamiento   â”‚
    â”‚  (.env en raiz)     â”‚   â”‚  (storage/node*)  â”‚
    â”‚                     â”‚   â”‚                   â”‚
    â”‚ SUPABASE_URL â”€â”€â”€â”€â”€â”€â–ºâ”‚   â”‚ storage/node1/    â”‚
    â”‚ SUPABASE_KEY â”€â”€â”€â”€â”€â”€â–ºâ”‚   â”‚ storage/node2/    â”‚
    â”‚                     â”‚   â”‚ storage/node3/    â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

FLUJO DE DATOS:
1. Usuario carga PDF en /upload
2. master/routes.py recibe, llama database.insertar_documento()
3. Replica en 3 nodos con database.insertar_nodo_replicacion()
4. consensus.clasificar_con_consenso() contacta 3 workers
5. Cada worker predice (predict) â†’ registrado con database.insertar_voto_consenso()
6. master calcula mayorÃ­a, llama database.actualizar_documento_clasificacion()
7. Todo persistido en Supabase (HA + auditable)
└─ Ejecutar test_conexion.py para validar conexión
 [ ] test_conexion.py pasa ✓
---
python test_conexion.py  # 2 min

## Archivos de DocumentaciÃ³n Creados

### GuÃ­as de IntegraciÃ³n (Lee en este orden)

| Archivo | Tiempo | Para QuiÃ©n | Contenido |
|---------|--------|-----------|----------|
| **guia_rapida_supabase.md** | 3 min | Usuario impaciente | Setup Supabase + test de conexiÃ³n (15 min total) |
| **guia_completa_supabase.md** | 15 min | Desarrollador | 7 pasos detallados con ejemplos Python |
| **EJEMPLO_INTEGRACION_ROUTES.py** | 20 min | Implementador | CÃ³digo antes/despuÃ©s comentado para routes.py |
| **EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py** | 15 min | Implementador | CÃ³mo agregar BD a consensus y election |

### Archivos TÃ©cnicos (Ya Existentes)

| Archivo | PropÃ³sito |
|---------|----------|
| **SCHEMA_SUPABASE_FINAL.sql** | Schema PostgreSQL completo (ejecutar en Supabase) |
| **master/database.py** | 25 funciones Python para interactuar con Supabase |
| **.env** (crear) | Variables: SUPABASE_URL, SUPABASE_KEY |

---

## Plan de AcciÃ³n Paso a Paso

```
PASO 1: SETUP SUPABASE (15 minutos)
â”œâ”€ Crear proyecto en https://supabase.com
â”œâ”€ Ejecutar SCHEMA_SUPABASE_FINAL.sql en SQL Editor
â”œâ”€ Copiar credenciales (SUPABASE_URL + SUPABASE_KEY)
â”œâ”€ Crear archivo .env con credenciales
â”œâ”€ pip install supabase python-dotenv
â””â”€ Ejecutar test_conexion.py para validar conexiÃ³n

PASO 2: INTEGRAR ROUTES.py (30-45 minutos)
â”œâ”€ Abrir master/routes.py
â”œâ”€ Consultar EJEMPLO_INTEGRACION_ROUTES.py
â”œâ”€ Reemplazar:
â”‚  â”œâ”€ /register: usar insertar_usuario()
â”‚  â”œâ”€ /login: usar obtener_usuario_por_nombre() + crear_token_sesion()
â”‚  â”œâ”€ /upload: usar insertar_documento() + insertar_nodo_replicacion()
â”‚  â””â”€ /delete: usar marcar_documento_eliminando()
â””â”€ Verificar que compilaciona (python -m py_compile master/routes.py)

PASO 3: INTEGRAR CONSENSUS.py (15 minutos)
â”œâ”€ Abrir master/consensus.py
â”œâ”€ Consultar EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py
â”œâ”€ Agregar: insertar_voto_consenso() despuÃ©s de cada voto
â”œâ”€ Agregar: actualizar_documento_clasificacion() despuÃ©s de consenso
â””â”€ Verificar que compilaciona

PASO 4: INTEGRAR ELECTION.py (10 minutos)
â”œâ”€ Abrir shared/election.py
â”œâ”€ Consultar EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py
â”œâ”€ Agregar: heartbeat_lider() en loop cada 5s
â”œâ”€ Agregar: obtener_lider() + actualizar_lider() en eleccion
â””â”€ Verificar que compilaciona

PASO 5: TEST E2E (20 minutos)
â”œâ”€ Iniciar master: python master/main.py
â”œâ”€ Iniciar 3 workers: python worker/main.py (x3 en puertos 5001-5003)
â”œâ”€ Registrar usuario: POST /register
â”œâ”€ Login: POST /login (obtener token)
â”œâ”€ Upload PDF: POST /upload con token
â”œâ”€ Verificar en Supabase:
â”‚  â”œâ”€ usuarios: debe mostrar nuevo usuario
â”‚  â”œâ”€ documentos: debe mostrar documento creado
â”‚  â”œâ”€ consenso_votos: debe mostrar 3 votos (uno por worker)
â”‚  â”œâ”€ nodos_almacenamiento: debe mostrar 3 replicas
â”‚  â””â”€ lider_actual: debe mostrar nodo actual vivo
â””â”€ LISTO!

TIEMPO TOTAL: ~2-3 horas la primera vez
VECES POSTERIORES: ~30 minutos (sin setup Supabase)
```

---

## Funciones Clave de database.py

### AutenticaciÃ³n
- `insertar_usuario(username, password_hash, rol_id)` â†’ UUID usuario
- `obtener_usuario_por_nombre(username)` â†’ Dict usuario
- `crear_token_sesion(usuario_id, token_hash, expira_en)` â†’ UUID token
- `obtener_token(token_hash)` â†’ Dict token con usuario_id
- `revocar_token(token_hash)` â†’ Bool Ã©xito

### JerarquÃ­a de Documentos
- `obtener_tematicas_usuario(usuario_id)` â†’ List[Dict]
- `insertar_tematica(usuario_id, nombre, es_general)` â†’ UUID tematica
- `obtener_subtematicas(tematica_id)` â†’ List[Dict]
- `insertar_subtematica(tematica_id, nombre)` â†’ UUID subtematica

### Almacenamiento de Documentos
- `insertar_documento(usuario_id, tematica_id, nombre_archivo, hash, tamano, subtematica_id)` â†’ UUID doc
- `obtener_documentos_usuario(usuario_id)` â†’ List[Dict]
- `actualizar_documento_clasificacion(doc_id, subtematica_id, confianza)` â†’ Bool
- `marcar_documento_eliminando(doc_id)` â†’ Bool
- `marcar_documento_eliminado(doc_id)` â†’ Bool

### ReplicaciÃ³n Distribuida
- `insertar_nodo_replicacion(doc_id, nodo, ruta_fisica)` â†’ UUID nodo
- `obtener_nodos_documento(doc_id)` â†’ List[Dict]
- `marcar_nodo_verificado(doc_id, nodo)` â†’ Bool
- `marcar_nodo_inactivo(doc_id, nodo)` â†’ Bool

### VotaciÃ³n y Consenso
- `insertar_voto_consenso(doc_id, nodo_worker, area_predicha, confianza)` â†’ UUID voto
- `obtener_votos_documento(doc_id)` â†’ List[Dict]

### Liderazgo Distribuido
- `obtener_lider()` â†’ Dict lider
- `actualizar_lider(nodo_id, nodo_hostname, nodo_url)` â†’ Bool
- `heartbeat_lider(nodo_id)` â†’ Bool

---

## ValidaciÃ³n RÃ¡pida

Para verificar que todo estÃ¡ conectado correctamente:

```python
# test_conexion.py

import os
from dotenv import load_dotenv
from master.database import (
    insertar_usuario,
    obtener_usuario_por_nombre,
    obtener_tematicas_usuario,
    insertar_documento,
    insertar_nodo_replicacion,
    insertar_voto_consenso,
    actualizar_lider,
    obtener_lider
)

load_dotenv()

# 1. Usuario
user_id = insertar_usuario("test_final", "hash123")
user = obtener_usuario_por_nombre("test_final")
assert user, "âŒ Usuario no se creo"
print("âœ“ Usuario creado y obtenido")

# 2. Tematicas
tematicas = obtener_tematicas_usuario(user_id)
assert len(tematicas) >= 1, "âŒ Sin tematica General"
print(f"âœ“ Tematicas obtenidas: {len(tematicas)}")

# 3. Documento
doc_id = insertar_documento(
    usuario_id=user_id,
    tematica_id=tematicas[0]['id'],
    nombre_archivo="test.pdf",
    hash_archivo="abc123",
    tamano_bytes=1000
)
assert doc_id, "âŒ Documento no se creo"
print(f"âœ“ Documento creado: {doc_id}")

# 4. Replicacion
for nodo in ['node1', 'node2', 'node3']:
    nodo_id = insertar_nodo_replicacion(doc_id, nodo, f"/storage/{nodo}/test.pdf")
    assert nodo_id, f"âŒ Nodo {nodo} no se creo"
print("âœ“ 3 nodos replicados")

# 5. Votos
for i, nodo in enumerate(['node1', 'node2', 'node3']):
    voto_id = insertar_voto_consenso(doc_id, nodo, "Area1", 0.85 + i*0.05)
    assert voto_id, f"âŒ Voto de {nodo} no se registro"
print("âœ“ 3 votos registrados")

# 6. Liderazgo
lider_updated = actualizar_lider(1, "worker1", "http://localhost:5001")
assert lider_updated, "âŒ Lider no se actualizo"
lider = obtener_lider()
assert lider['nodo_id'] == 1, "âŒ Lider incorrecto"
print(f"âœ“ Lider establecido: nodo {lider['nodo_id']}")

print("\nðŸŽ‰ VALIDACION COMPLETA: Toda la BD funciona correctamente!")
```

Ejecutar:
```bash
python test_conexion.py
```

---

## Checklist Final

- [ ] Proyecto Supabase creado
- [ ] SQL ejecutado sin errores (9 tablas + 2 triggers + 4 vistas)
- [ ] .env creado con SUPABASE_URL y SUPABASE_KEY
- [ ] `pip install supabase python-dotenv` ejecutado
- [ ] test_conexion.py pasa âœ“
- [ ] routes.py actualizado con database functions
- [ ] consensus.py actualizado con insertar_voto_consenso
- [ ] election.py actualizado con heartbeat_lider
- [ ] sync.py actualizado con marcar_nodo_verificado
- [ ] Test E2E completo ejecutado
- [ ] Datos persistidos en Supabase verificados

---

## Proximos Pasos (Futuros)

1. **Mejorar classifier.py**: Cambiar de `predict()` a `predict_proba()` para obtener confianza real
2. **Activar RLS**: Row Level Security en Supabase (cada usuario solo ve sus datos)
3. **Agregar cuotas**: Tabla cuotas_usuario con lÃ­mites por usuario
4. **Monitoreo**: Logs de errores en tabla logs_errores_clasificacion
5. **CI/CD**: GitHub Actions para deploy automÃ¡tico

---

## Dudas Frecuentes

### Â¿DÃ³nde hago cambios?
1. **BD**: SCHEMA_SUPABASE_FINAL.sql (en Supabase SQL Editor)
2. **Python**: master/database.py (25 funciones)
3. **IntegraciÃ³n**: EJEMPLO_INTEGRACION_ROUTES.py (copiar logica a routes.py)

### Â¿CÃ³mo valido que funciona?
```bash
python test_conexion.py  # 2 min
python test_conexion.py  # 10 min
```

### Â¿QuÃ© pasa si Supabase falla?
- Si RLS no estÃ¡ habilitado: todos ven todos los datos (desarrollo, no producciÃ³n)
- Si servidor falla: Supabase tiene backups automÃ¡ticos
- Si quiero salir: Exportar base de datos completa como SQL

---

**Ãšltima actualizaciÃ³n**: 22 abril 2026
**Status**: âœ… Listo para implementar
**Contacto**: Claudio (implementador) o Erick (usuario final)


