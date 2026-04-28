# Guia de Integracion - Supabase + Proyecto

## PASO 1: Crear Proyecto Supabase (5 minutos)

### 1.1 Ir a https://supabase.com
- Click en "Sign Up"
- Crear cuenta con GitHub o email

### 1.2 Crear nuevo proyecto
- Click en "New project"
- Nombre: `clasificador-final` (o el que prefieras)
- Contrasena: guardar en lugar seguro
- Region: elegir la mas cercana

### 1.3 Esperar a que inicialize (~1-2 minutos)
Una vez listo, veras el dashboard.

---

## PASO 2: Ejecutar Schema SQL (2 minutos)

### 2.1 Abrir SQL Editor
En Supabase dashboard:
- Click en "SQL Editor" (lado izquierdo)
- Click en "New Query"

### 2.2 Copiar y pegar el SQL
- Abre el archivo: `SCHEMA_SUPABASE_FINAL.sql`
- Ctrl+A para seleccionar todo
- Ctrl+C para copiar
- Pega en Supabase SQL Editor (Ctrl+V)
- Click en boton "RUN" (arriba a la derecha)

**Resultado esperado**: Verde checkmark con "Executed successfully"

### 2.3 Verificar que se crearon tablas
- Click en "Table Editor" (lado izquierdo)
- Deberias ver 9 tablas:
  * roles
  * usuarios
  * tokens_sesion
  * tematicas
  * subtematicas
  * documentos
  * nodos_almacenamiento
  * consenso_votos
  * lider_actual

---

## PASO 3: Obtener Credenciales (2 minutos)

### 3.1 Ir a Project Settings
En Supabase:
- Click en gear icon (arriba a la derecha) → "Project Settings"
- Click en "API" en el menu izquierdo

### 3.2 Copiar credenciales
Encontraras:
```
Project URL:     https://xxxxxxxxxxxxx.supabase.co
Anon Key:        eyJhbGc.....
Service Role Key: eyJhbGc..... (ignorar por ahora)
```

Copiar:
- **SUPABASE_URL** = Project URL
- **SUPABASE_KEY** = Anon Key (copiar el completo)

---

## PASO 4: Configurar Variables de Entorno (2 minutos)

### 4.1 Crear archivo .env en la raiz del proyecto

Archivo: `c:\Users\erick\Downloads\clasificador-final\.env`

Contenido:
```env
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
PYTHONPATH=.
```
from master.database import obtener_usuario_por_nombre

usuario = obtener_usuario_por_nombre(username)
if usuario:
    # Crear token y guardar en BD
    token_id = crear_token_sesion(
        usuario_id=usuario['id'],
        token_hash=token_hash,
        expira_en="2026-04-23T12:00:00Z"  # 24h desde ahora

---

## PASO 5: Usar database.py en el Codigo Existente

### 5.1 En master/routes.py

El login debe consultar Supabase directamente:

```python
from master.database import obtener_usuario_por_nombre, crear_token_sesion

usuario = obtener_usuario_por_nombre(username)
if usuario:
    token_id = crear_token_sesion(
        usuario_id=usuario['id'],
        token_hash=token_hash,
        expira_en="2026-04-23T12:00:00Z"  # 24h desde ahora
    )
```

### 5.2 En master/consensus.py

**ANTES** (implícito en JSON):
```python
# Guardar votos en memoria
votos = {}
```

**DESPUES** (Supabase):
```python
from master.database import (
    insertar_voto_consenso,
    obtener_votos_documento,
    actualizar_documento_clasificacion
)

# Registrar cada voto
for nodo_worker, resultado in resultados.items():
    insertar_voto_consenso(
        documento_id=doc_id,
        nodo_worker=nodo_worker,
        area_predicha=resultado['area'],
        confianza_worker=resultado.get('confianza', 0.0)
    )

# Obtener todos los votos para calcular consenso
votos = obtener_votos_documento(doc_id)

# Registrar clasificacion final
actualizar_documento_clasificacion(
    documento_id=doc_id,
    subtematica_id=subtematica_final['id'],
    confianza=confianza_consenso
)
```

### 5.3 En master/routes.py - POST /upload

**ANTES** (JSON):
```python
@router.post("/upload")
def upload_file(...):
    # Guardar en JSON
    metadata = {...}
    save_metadata(usuario, metadata)
```

**DESPUES** (Supabase):
```python
from master.database import (
    insertar_documento,
    insertar_nodo_replicacion,
    marcar_nodo_verificado
)

@router.post("/upload")
def upload_file(...):
    # 1. Registrar documento en BD
    doc_id = insertar_documento(
        usuario_id=usuario['id'],
        tematica_id=tematica['id'],
        nombre_archivo=file.filename,
        hash_archivo=calcular_hash_archivo(file),
        tamano_bytes=len(file),
        subtematica_id=subtematica.get('id')
    )
    
    # 2. Replicar en 3 nodos
    for nodo in ['node1', 'node2', 'node3']:
        ruta = f"../storage/{nodo}/doc_{doc_id}.pdf"
        shutil.copy(file, ruta)
        insertar_nodo_replicacion(doc_id, nodo, ruta)
    
    # 3. Clasificar con consenso
    area_final = clasificar_con_consenso(file)
    
    # 4. Actualizar documento con clasificacion
    actualizar_documento_clasificacion(
        doc_id,
        area_final['subtematica_id'],
        area_final['confianza']
    )
    
    return {"documento_id": doc_id, "estado": "clasificado"}
```

### 5.4 En shared/election.py - Liderazgo

**ANTES** (archivo SQL):
```python
# Leer de lider_actual.sql
with open("lider_actual.sql") as f:
    lider = json.load(f)
```

**DESPUES** (Supabase):
```python
from master.database import (
    obtener_lider,
    actualizar_lider,
    heartbeat_lider
)

# Obtener lider actual
lider = obtener_lider()
if lider:
    nodo_url = lider['nodo_url']

# Registrar nueva eleccion
actualizar_lider(
    nodo_id=1,
    nodo_hostname='worker1',
    nodo_url='http://localhost:5001'
)

# Heartbeat (cada 5 segundos)
heartbeat_lider(nodo_id=1)
```

---

## PASO 6: Flujo Completo - Ejemplo de /upload

```python
from fastapi import APIRouter, UploadFile, File
from master.auth import obtener_usuario_del_token
from master.database import (
    insertar_documento,
    insertar_nodo_replicacion,
    actualizar_documento_clasificacion,
    obtener_votos_documento
)
from master.consensus import clasificar_con_consenso

router = APIRouter()

@router.post("/upload")
async def upload_documento(file: UploadFile = File(...), token: str = Header(...)):
    # 1. Obtener usuario del token
    usuario = obtener_usuario_del_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # 2. Validar archivo
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo PDF permitidos")
    
    # 3. Crear registro en BD
    doc_id = insertar_documento(
        usuario_id=usuario['id'],
        tematica_id='tematica-general-id',  # obtener de BD
        nombre_archivo=file.filename,
        hash_archivo=hashlib.sha256(file.file.read()).hexdigest(),
        tamano_bytes=file.size,
    )
    
    if not doc_id:
        raise HTTPException(status_code=500, detail="Error creando documento")
    
    # 4. Replicar en 3 nodos
    for nodo in ['node1', 'node2', 'node3']:
        ruta = f"../storage/{nodo}/{doc_id}.pdf"
        with open(ruta, 'wb') as f:
            f.write(file.file.read())
        
        insertar_nodo_replicacion(
            documento_id=doc_id,
            nodo=nodo,
            ruta_fisica=ruta
        )
    
    # 5. Clasificar con consenso
    areas = clasificar_con_consenso(file)
    
    # 6. Actualizar documento con resultado
    actualizar_documento_clasificacion(
        documento_id=doc_id,
        subtematica_id=areas['subtematica_id'],
        confianza=areas['confianza']
    )
    
    return {
        "documento_id": doc_id,
        "nombre": file.filename,
        "clasificacion": areas['nombre'],
        "confianza": areas['confianza']
    }
```

---

## PASO 7: Verificar que Funciona

### 7.1 Test simple en Python

Crear archivo: `test_db.py`

```python
import os
from dotenv import load_dotenv
from master.database import (
    insertar_usuario,
    obtener_usuario_por_nombre,
    obtener_tematicas_usuario,
    insertar_tematica
)

load_dotenv()

# Test 1: Crear usuario
usuario_id = insertar_usuario(
    username="test_user",
    password_hash="hash123"
)
print(f"Usuario creado: {usuario_id}")

# Test 2: Obtener usuario
usuario = obtener_usuario_por_nombre("test_user")
print(f"Usuario obtenido: {usuario['username']}")

# Test 3: Obtener tematicas
tematicas = obtener_tematicas_usuario(usuario_id)
print(f"Tematicas: {len(tematicas)}")  # Debe ser 1 (General)

# Test 4: Crear subtematica
tematica_general = tematicas[0]
print(f"Tematica General ID: {tematica_general['id']}")
```

Ejecutar:
```bash
python test_db.py
```

Resultado esperado:
```
Usuario creado: 550e8400-e29b-41d4-a716-446655440000
Usuario obtenido: test_user
Tematicas: 1
Tematica General ID: 660e8400-e29b-41d4-a716-446655440001
```

---

## CHECKLIST - Antes de Usar en Produccion

- [ ] Proyecto Supabase creado
- [ ] SQL ejecutado sin errores
- [ ] 9 tablas creadas en SQL Editor
- [ ] Credenciales copiadas en .env
- [ ] `pip install supabase python-dotenv` ejecutado
- [ ] Test de conexion (test_db.py) pasa
- [ ] Routes.py actualizado para usar database.py
- [ ] Consensus.py registra votos en BD
- [ ] Election.py usa lider_actual de BD

---

## PROBLEMAS COMUNES

### Error: "SUPABASE_URL/SUPABASE_KEY not set"
**Causa**: Variables de entorno no configuradas
**Solucion**: Verificar que .env existe y tiene valores correctos

### Error: "table usuarios does not exist"
**Causa**: SQL no fue ejecutado en Supabase
**Solucion**: Ir a PASO 2 y ejecutar SCHEMA_SUPABASE_FINAL.sql

### Error: "Unauthorized"
**Causa**: Anon Key no tiene permisos
**Solucion**: En Supabase → Settings → Auth → Policies, verificar RLS (Row Level Security) deshabilitado para desarrollo

### Timeout en operaciones
**Causa**: Red lenta o Supabase lejos
**Solucion**: Agregar timeout en requests:
```python
db = create_client(SUPABASE_URL, SUPABASE_KEY, timeout=10)
```

---

## NOTAS IMPORTANTES

1. **Default 24h tokens**: `expira_en` tiene DEFAULT de 24 horas. Si necesitas otra duracion, pasalo en Python.

2. **Confianza worker**: `confianza_worker` tiene DEFAULT 0.00 porque classifier.py ahora usa predict(). Cuando migres a predict_proba(), cambiar a NOT NULL sin default.

3. **Soft deletes**: El borrado usa 3 estados: `'activo'`, `'eliminando'`, `'eliminado'`. Permite auditar sin perder datos.

4. **Replicacion**: Registra en 3 nodos. Usar `marcar_nodo_verificado()` cuando sync.py confirme el archivo existe.

5. **Liderazgo**: El trigger auto-actualiza `ultimo_heartbeat` al hacer UPDATE. No hay que hacerlo manualmente.
