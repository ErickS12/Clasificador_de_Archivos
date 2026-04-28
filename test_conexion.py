"""
TEST DE CONEXION A SUPABASE
============================
Ejecutar: python test_conexion.py

Este script valida que la base de datos esté configurada correctamente.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=" * 60)
print("TEST DE CONEXION A SUPABASE")
print("=" * 60)

# ── PASO 1: Verificar que .env existe y tiene valores ────────────────

print("\n[1] Verificando variables de entorno...")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    print("❌ ERROR: SUPABASE_URL no está configurada en .env")
    sys.exit(1)

if not SUPABASE_KEY:
    print("❌ ERROR: SUPABASE_KEY no está configurada en .env")
    sys.exit(1)

print(f"✓ SUPABASE_URL: {SUPABASE_URL[:50]}...")
print(f"✓ SUPABASE_KEY: {SUPABASE_KEY[:20]}...")

# ── PASO 2: Intentar conectar a Supabase ────────────────────────────

print("\n[2] Conectando a Supabase...")

try:
    from supabase import create_client, Client
    
    db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Conexión establecida a Supabase")
    
except ImportError:
    print("❌ ERROR: libreria 'supabase' no instalada")
    print("   Ejecuta: pip install supabase python-dotenv")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR al conectar: {e}")
    sys.exit(1)

# ── PASO 3: Probar lectura de tabla (usuarios) ───────────────────────

print("\n[3] Probando lectura de tabla 'usuarios'...")

try:
    response = db.table("usuarios").select("*").limit(1).execute()
    print(f"✓ Tabla 'usuarios' existe y es legible")
    print(f"  Registros encontrados: {len(response.data)}")
    
except Exception as e:
    print(f"❌ ERROR al leer tabla 'usuarios': {e}")
    print("   ¿Ejecutaste SCHEMA_SUPABASE_FINAL.sql en Supabase SQL Editor?")
    sys.exit(1)

# ── PASO 4: Crear usuario de prueba ──────────────────────────────────

print("\n[4] Probando creación de usuario...")

import hashlib
import uuid

try:
    username = f"test_conexion_{uuid.uuid4().hex[:8]}"
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        b'password_test',
        b'salt_test',
        100000
    ).hex()
    
    response = db.table("usuarios").insert({
        "username": username,
        "password_hash": password_hash,
        "rol_id": 2,  # user
        "activo": True
    }).execute()
    
    if response.data:
        usuario_id = response.data[0]['id']
        print(f"✓ Usuario creado: {username}")
        print(f"  ID: {usuario_id}")
    else:
        print(f"⚠️  Usuario no se retornó (pero pudo crearse)")
        
except Exception as e:
    print(f"❌ ERROR al crear usuario: {e}")
    sys.exit(1)

# ── PASO 5: Obtener usuario creado ───────────────────────────────────

print("\n[5] Probando lectura del usuario creado...")

try:
    response = db.table("usuarios").select("*").eq("username", username).single().execute()
    
    if response.data:
        usuario = response.data
        print(f"✓ Usuario obtenido: {usuario['username']}")
        print(f"  Rol ID: {usuario['rol_id']}")
        print(f"  Activo: {usuario['activo']}")
    else:
        print(f"❌ Usuario no encontrado (pero debería existir)")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR al obtener usuario: {e}")
    sys.exit(1)

# ── PASO 6: Verificar que se creó tematica General ───────────────────

print("\n[6] Verificando tematica 'General' automática...")

try:
    response = db.table("tematicas").select("*").eq("usuario_id", usuario_id).eq("es_general", True).execute()
    
    if response.data and len(response.data) > 0:
        tematica = response.data[0]
        print(f"✓ Tematica 'General' creada automáticamente")
        print(f"  ID: {tematica['id']}")
        print(f"  Nombre: {tematica['nombre']}")
    else:
        print(f"⚠️  Tematica 'General' no encontrada (el trigger puede no funcionar)")
        
except Exception as e:
    print(f"⚠️  Error al verificar tematica: {e}")

# ── PASO 7: Verificar tokens ─────────────────────────────────────────

print("\n[7] Probando tabla 'tokens_sesion'...")

try:
    response = db.table("tokens_sesion").select("*").limit(1).execute()
    print(f"✓ Tabla 'tokens_sesion' es legible")
    
except Exception as e:
    print(f"❌ ERROR: tabla 'tokens_sesion' no existe o no es legible: {e}")
    sys.exit(1)

# ── PASO 8: Verificar otras tablas clave ────────────────────────────

print("\n[8] Verificando otras tablas...")

tablas_clave = [
    "roles",
    "tematicas",
    "subtematicas",
    "documentos",
    "nodos_almacenamiento",
    "consenso_votos",
    "lider_actual"
]

tablas_ok = 0
for tabla in tablas_clave:
    try:
        response = db.table(tabla).select("*").limit(1).execute()
        print(f"  ✓ {tabla}")
        tablas_ok += 1
    except Exception as e:
        print(f"  ❌ {tabla}: {str(e)[:50]}...")

if tablas_ok == len(tablas_clave):
    print(f"\n✓ Todas las {len(tablas_clave)} tablas existen")
else:
    print(f"\n⚠️  Solo {tablas_ok}/{len(tablas_clave)} tablas existen")
    print("   ¿Falta ejecutar el SQL?")

# ── RESUMEN FINAL ────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("RESULTADO FINAL")
print("=" * 60)

if tablas_ok == len(tablas_clave):
    print("""
🎉 ¡EXITO! La base de datos está configurada correctamente.

Puedes proceder a:
1. Modificar master/routes.py para usar database.py
2. Modificar master/consensus.py para guardar votos
3. Modificar shared/election.py para liderazgo

Próximos pasos:
├─ python master/main.py (iniciar master)
├─ python worker/main.py (iniciar 3 workers en puertos 5001-5003)
└─ Probar endpoints: POST /register, POST /login, POST /upload
""")
else:
    print(f"""
⚠️  Algunas tablas faltan. Pasos para corregir:

1. Ir a https://supabase.com → Dashboard
2. Ir a SQL Editor → New Query
3. Abrir archivo: SCHEMA_SUPABASE_FINAL.sql
4. Copiar TODO el contenido
5. Pegar en SQL Editor
6. Click "RUN"
7. Esperar verde: "Executed successfully ✓"
8. Ejecutar este script de nuevo

O ejecutar en terminal:
$ psql postgresql://[user]:[pass]@[host]/[db] < SCHEMA_SUPABASE_FINAL.sql
""")

print("=" * 60)
