# Mapa de Integración - Clasificador Final

## Vista General: Archivos y Conexiones

```
┌─────────────────────────────────────────────────────────────────┐
│                       SUPABASE (Nube)                           │
│  PostgreSQL con 9 tablas, 2 triggers, 4 vistas, índices        │
│  (roles, usuarios, tokens, tematicas, subtematicas,            │
│   documentos, nodos_almacenamiento, consenso_votos, lider)     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
       ┌─────────▼──────────┐      ┌────────▼──────────┐
       │  MASTER            │      │  WORKERS          │
       │  (Orquestador)     │      │  (Clasificación)  │
       │                    │      │                   │
       │ main.py            │      │ main.py (x3)      │
       │ routes.py ◄────────┼──────┼─ classifier.py    │
       │ gateway.py         │      │ sync.py           │
       │ auth.py            │      │                   │
       │ consensus.py       │      │ localhost:5001    │
       │ adapter.py         │      │ localhost:5002    │
       │ database.py ──────┐│      │ localhost:5003    │
       │                  │└──────►                   │
       └─────────┬────────┘       └───────┬──────────┘
                 │                        │
    ┌────────────┴────────┐   ┌──────────┴────────┐
    │  Archivos Python    │   │  Almacenamiento   │
    │  (.env en raiz)     │   │  (storage/node*)  │
    │                     │   │                   │
    │ SUPABASE_URL ──────►│   │ storage/node1/    │
    │ SUPABASE_KEY ──────►│   │ storage/node2/    │
    │                     │   │ storage/node3/    │
    └─────────────────────┘   └───────────────────┘

FLUJO DE DATOS:
1. Usuario carga PDF en /upload
2. master/routes.py recibe, llama database.insertar_documento()
3. Replica en 3 nodos con database.insertar_nodo_replicacion()
4. consensus.clasificar_con_consenso() contacta 3 workers
5. Cada worker predice (predict) → registrado con database.insertar_voto_consenso()
6. master calcula mayoría, llama database.actualizar_documento_clasificacion()
7. Todo persistido en Supabase (HA + auditable)
```

---

## Archivos de Documentación Creados

### Guías de Integración (Lee en este orden)

| Archivo | Tiempo | Para Quién | Contenido |
|---------|--------|-----------|----------|
| **PASOS_RAPIDOS.md** | 3 min | Usuario impaciente | Setup Supabase + test de conexión (15 min total) |
| **GUIA_INTEGRACION.md** | 15 min | Desarrollador | 7 pasos detallados con ejemplos Python |
| **EJEMPLO_INTEGRACION_ROUTES.py** | 20 min | Implementador | Código antes/después comentado para routes.py |
| **EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py** | 15 min | Implementador | Cómo agregar BD a consensus y election |

### Archivos Técnicos (Ya Existentes)

| Archivo | Propósito |
|---------|----------|
| **SCHEMA_SUPABASE_FINAL.sql** | Schema PostgreSQL completo (ejecutar en Supabase) |
| **master/database.py** | 25 funciones Python para interactuar con Supabase |
| **.env** (crear) | Variables: SUPABASE_URL, SUPABASE_KEY |

---

## Plan de Acción Paso a Paso

```
PASO 1: SETUP SUPABASE (15 minutos)
├─ Crear proyecto en https://supabase.com
├─ Ejecutar SCHEMA_SUPABASE_FINAL.sql en SQL Editor
├─ Copiar credenciales (SUPABASE_URL + SUPABASE_KEY)
├─ Crear archivo .env con credenciales
├─ pip install supabase python-dotenv
└─ Ejecutar test_db_rapido.py para validar conexión

PASO 2: INTEGRAR ROUTES.py (30-45 minutos)
├─ Abrir master/routes.py
├─ Consultar EJEMPLO_INTEGRACION_ROUTES.py
├─ Reemplazar:
│  ├─ /register: usar insertar_usuario()
│  ├─ /login: usar obtener_usuario_por_nombre() + crear_token_sesion()
│  ├─ /upload: usar insertar_documento() + insertar_nodo_replicacion()
│  └─ /delete: usar marcar_documento_eliminando()
└─ Verificar que compilaciona (python -m py_compile master/routes.py)

PASO 3: INTEGRAR CONSENSUS.py (15 minutos)
├─ Abrir master/consensus.py
├─ Consultar EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py
├─ Agregar: insertar_voto_consenso() después de cada voto
├─ Agregar: actualizar_documento_clasificacion() después de consenso
└─ Verificar que compilaciona

PASO 4: INTEGRAR ELECTION.py (10 minutos)
├─ Abrir shared/election.py
├─ Consultar EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py
├─ Agregar: heartbeat_lider() en loop cada 5s
├─ Agregar: obtener_lider() + actualizar_lider() en eleccion
└─ Verificar que compilaciona

PASO 5: TEST E2E (20 minutos)
├─ Iniciar master: python master/main.py
├─ Iniciar 3 workers: python worker/main.py (x3 en puertos 5001-5003)
├─ Registrar usuario: POST /register
├─ Login: POST /login (obtener token)
├─ Upload PDF: POST /upload con token
├─ Verificar en Supabase:
│  ├─ usuarios: debe mostrar nuevo usuario
│  ├─ documentos: debe mostrar documento creado
│  ├─ consenso_votos: debe mostrar 3 votos (uno por worker)
│  ├─ nodos_almacenamiento: debe mostrar 3 replicas
│  └─ lider_actual: debe mostrar nodo actual vivo
└─ LISTO!

TIEMPO TOTAL: ~2-3 horas la primera vez
VECES POSTERIORES: ~30 minutos (sin setup Supabase)
```

---

## Funciones Clave de database.py

### Autenticación
- `insertar_usuario(username, password_hash, rol_id)` → UUID usuario
- `obtener_usuario_por_nombre(username)` → Dict usuario
- `crear_token_sesion(usuario_id, token_hash, expira_en)` → UUID token
- `obtener_token(token_hash)` → Dict token con usuario_id
- `revocar_token(token_hash)` → Bool éxito

### Jerarquía de Documentos
- `obtener_tematicas_usuario(usuario_id)` → List[Dict]
- `insertar_tematica(usuario_id, nombre, es_general)` → UUID tematica
- `obtener_subtematicas(tematica_id)` → List[Dict]
- `insertar_subtematica(tematica_id, nombre)` → UUID subtematica

### Almacenamiento de Documentos
- `insertar_documento(usuario_id, tematica_id, nombre_archivo, hash, tamano, subtematica_id)` → UUID doc
- `obtener_documentos_usuario(usuario_id)` → List[Dict]
- `actualizar_documento_clasificacion(doc_id, subtematica_id, confianza)` → Bool
- `marcar_documento_eliminando(doc_id)` → Bool
- `marcar_documento_eliminado(doc_id)` → Bool

### Replicación Distribuida
- `insertar_nodo_replicacion(doc_id, nodo, ruta_fisica)` → UUID nodo
- `obtener_nodos_documento(doc_id)` → List[Dict]
- `marcar_nodo_verificado(doc_id, nodo)` → Bool
- `marcar_nodo_inactivo(doc_id, nodo)` → Bool

### Votación y Consenso
- `insertar_voto_consenso(doc_id, nodo_worker, area_predicha, confianza)` → UUID voto
- `obtener_votos_documento(doc_id)` → List[Dict]

### Liderazgo Distribuido
- `obtener_lider()` → Dict lider
- `actualizar_lider(nodo_id, nodo_hostname, nodo_url)` → Bool
- `heartbeat_lider(nodo_id)` → Bool

---

## Validación Rápida

Para verificar que todo está conectado correctamente:

```python
# test_validacion_completa.py

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
assert user, "❌ Usuario no se creo"
print("✓ Usuario creado y obtenido")

# 2. Tematicas
tematicas = obtener_tematicas_usuario(user_id)
assert len(tematicas) >= 1, "❌ Sin tematica General"
print(f"✓ Tematicas obtenidas: {len(tematicas)}")

# 3. Documento
doc_id = insertar_documento(
    usuario_id=user_id,
    tematica_id=tematicas[0]['id'],
    nombre_archivo="test.pdf",
    hash_archivo="abc123",
    tamano_bytes=1000
)
assert doc_id, "❌ Documento no se creo"
print(f"✓ Documento creado: {doc_id}")

# 4. Replicacion
for nodo in ['node1', 'node2', 'node3']:
    nodo_id = insertar_nodo_replicacion(doc_id, nodo, f"/storage/{nodo}/test.pdf")
    assert nodo_id, f"❌ Nodo {nodo} no se creo"
print("✓ 3 nodos replicados")

# 5. Votos
for i, nodo in enumerate(['node1', 'node2', 'node3']):
    voto_id = insertar_voto_consenso(doc_id, nodo, "Area1", 0.85 + i*0.05)
    assert voto_id, f"❌ Voto de {nodo} no se registro"
print("✓ 3 votos registrados")

# 6. Liderazgo
lider_updated = actualizar_lider(1, "worker1", "http://localhost:5001")
assert lider_updated, "❌ Lider no se actualizo"
lider = obtener_lider()
assert lider['nodo_id'] == 1, "❌ Lider incorrecto"
print(f"✓ Lider establecido: nodo {lider['nodo_id']}")

print("\n🎉 VALIDACION COMPLETA: Toda la BD funciona correctamente!")
```

Ejecutar:
```bash
python test_validacion_completa.py
```

---

## Checklist Final

- [ ] Proyecto Supabase creado
- [ ] SQL ejecutado sin errores (9 tablas + 2 triggers + 4 vistas)
- [ ] .env creado con SUPABASE_URL y SUPABASE_KEY
- [ ] `pip install supabase python-dotenv` ejecutado
- [ ] test_db_rapido.py pasa ✓
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
3. **Agregar cuotas**: Tabla cuotas_usuario con límites por usuario
4. **Monitoreo**: Logs de errores en tabla logs_errores_clasificacion
5. **CI/CD**: GitHub Actions para deploy automático

---

## Dudas Frecuentes

### ¿Dónde hago cambios?
1. **BD**: SCHEMA_SUPABASE_FINAL.sql (en Supabase SQL Editor)
2. **Python**: master/database.py (25 funciones)
3. **Integración**: EJEMPLO_INTEGRACION_ROUTES.py (copiar logica a routes.py)

### ¿Cómo valido que funciona?
```bash
python test_db_rapido.py  # 2 min
python test_validacion_completa.py  # 10 min
```

### ¿Qué pasa si Supabase falla?
- Si RLS no está habilitado: todos ven todos los datos (desarrollo, no producción)
- Si servidor falla: Supabase tiene backups automáticos
- Si quiero salir: Exportar base de datos completa como SQL

---

**Última actualización**: 22 abril 2026
**Status**: ✅ Listo para implementar
**Contacto**: Claudio (implementador) o Erick (usuario final)
