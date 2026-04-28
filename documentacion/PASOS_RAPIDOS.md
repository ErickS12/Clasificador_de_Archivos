# PASOS RAPIDOS - De 0 a Supabase en 15 minutos

## Paso 1: Crear Proyecto Supabase (3 min)

```
1. Ir a: https://supabase.com/sign-up
2. Crear cuenta (GitHub es mas rapido)
3. Click "New Project"
4. Nombre: clasificador-final
5. Password: guardar en lugar seguro
6. Region: la mas cercana a ti
7. Esperar 1-2 minutos a que inicialize
```

---

## Paso 2: Ejecutar SQL en Supabase (2 min)

```
1. En Supabase dashboard: click "SQL Editor"
2. Click "New Query"
3. Abre archivo: SCHEMA_SUPABASE_FINAL.sql
4. Ctrl+A → Ctrl+C (copiar todo)
5. Pega en SQL Editor: Ctrl+V
6. Click boton "RUN" (arriba a la derecha)
7. Esperar verde: "Executed successfully ✓"
```

---

## Paso 3: Copiar Credenciales (2 min)

En Supabase dashboard:

```
1. Click gear icon (arriba derecha) → "Project Settings"
2. Click "API" en menu izquierdo

COPIAR ESTOS VALORES:

Project URL:  https://xxxxxxxxxxxxx.supabase.co
Anon Key:     eyJhbGc....... (la larga)
```

---

## Paso 4: Crear .env (1 min)

Archivo: `c:\Users\erick\Downloads\clasificador-final\.env`

Contenido:
```env
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGc.....
PYTHONPATH=.
```

**REEMPLAZA** los valores con los que copiaste en Paso 3.

---

## Paso 5: Instalar Paquetes (2 min)

En terminal:
```bash
cd c:\Users\erick\Downloads\clasificador-final
pip install supabase python-dotenv
```

---

## Paso 6: Test Rapido (3 min)

Crea archivo: `test_db_rapido.py`

```python
import os
from dotenv import load_dotenv
from master.database import obtener_usuario_por_nombre, insertar_usuario

load_dotenv()

# Test 1: Crear usuario
usuario_id = insertar_usuario(
    username="test123",
    password_hash="hash_abc123"
)
print(f"✓ Usuario creado: {usuario_id}")

# Test 2: Obtener usuario
usuario = obtener_usuario_por_nombre("test123")
print(f"✓ Usuario obtenido: {usuario['username']}")
```

Ejecutar:
```bash
python test_db_rapido.py
```

Resultado esperado:
```
✓ Usuario creado: 550e8400-e29b-41d4-a716-446655440000
✓ Usuario obtenido: test123
```

Si ves ✓ en ambas lineas: **FELICIDADES! BD conectada correctamente.**

---

## Paso 7: Validar Routes

Archivo: `master/routes.py`

El login ya consulta Supabase directamente:

```python
from master.database import obtener_usuario_por_nombre

usuario = obtener_usuario_por_nombre(username)
```

Ver archivo: `EJEMPLO_INTEGRACION_ROUTES.py` para mas detalles.

---

## VERIFICACION FINAL

En Supabase dashboard:

1. Click en "Table Editor" (lado izquierdo)
2. Deberias ver estas 9 tablas:
   - [ ] roles
   - [ ] usuarios
   - [ ] tokens_sesion
   - [ ] tematicas
   - [ ] subtematicas
   - [ ] documentos
   - [ ] nodos_almacenamiento
   - [ ] consenso_votos
   - [ ] lider_actual

3. Hacer click en "usuarios" → deberia mostrar la fila del usuario test123

Si ves todo: **TODO LISTO PARA USAR!**

---

## PROXIMOS PASOS

1. ✅ Supabase configurado
2. ✅ BD conectada desde Python
3. ⬜ Actualizar routes.py (EJEMPLO_INTEGRACION_ROUTES.py)
4. ⬜ Actualizar consensus.py (EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py)
5. ⬜ Actualizar election.py (EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py)

---

## PROBLEMAS COMUNES

### "ModuleNotFoundError: No module named 'supabase'"
```bash
pip install supabase python-dotenv
```

### "SUPABASE_URL is None"
- Verificar que `.env` existe en la raiz del proyecto
- Verificar que tiene `SUPABASE_URL=` (no vacio)
- Ejecutar: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('SUPABASE_URL'))"`

### "table usuarios does not exist"
- Ir a PASO 2: ejecutar SQL en Supabase

### "Unauthorized" o "permission denied"
- En Supabase → Auth → usuarios → buscar fila que creaste
- Cambiar email_confirmed a TRUE
- (O ignorar por ahora, test local funciona igual)

---

## RESUMEN RAPIDO

```
1. Supabase: 5 min
2. SQL: 2 min
3. Credenciales: 2 min
4. .env: 1 min
5. Paquetes: 2 min
6. Test: 3 min
────────────────
TOTAL: 15 minutos hasta BD funcional
```

---

## ARCHIVOS IMPORTANTES

- `SCHEMA_SUPABASE_FINAL.sql` ← SQL a ejecutar en Supabase
- `master/database.py` ← Funciones Python para usar BD
- `EJEMPLO_INTEGRACION_ROUTES.py` ← Como integrar en routes.py
- `EJEMPLO_INTEGRACION_CONSENSUS_ELECTION.py` ← Como integrar consenso/liderazgo
- `GUIA_INTEGRACION.md` ← Documentacion completa

---

## CONTACTO CON SUPABASE

Si necesitas help:
- Dashboard: https://supabase.com
- Docs: https://supabase.com/docs
- Discord: https://discord.supabase.io
