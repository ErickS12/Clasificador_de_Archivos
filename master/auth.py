"""
Autenticación

Se manejan las contraseñas y las sesiones de usuario

- Las contraseñas se hashean con PBKDF2-SHA256 + salt aleatorio (con stdlib, que es una librería estándar de Python).

PBKDF2 es un algoritmo de hashing diseñado para ser lento y resistente a ataques de fuerza bruta, lo que lo hace adecuado para almacenar contraseñas de forma segura. 
El SHA256 es la función de hashing subyacente que se utiliza para generar el hash de la contraseña.
El salt aleatorio asegura que incluso si dos usuarios tienen la misma contraseña, sus hashes serán diferentes.

- Los tokens de sesión son UUIDs guardados en users.json.

los UUIDs (Universally Unique Identifiers) son identificadores únicos que se generan de forma aleatoria.
Al guardar estos tokens en users.json, el sistema puede verificar la autenticidad de las solicitudes posteriores utilizando estos tokens.

- El primer usuario registrado recibe el rol de administrador automáticamente.
"""

import hashlib
import os 
import uuid
from fastapi import HTTPException, Header


def hashear_contraseña(contraseña: str) -> str:
    """Genera salt aleatorio y devuelve 'salt$hash'."""
    iteraciones = 100_000
    salt = os.urandom(16).hex()
    clave  = hashlib.pbkdf2_hmac("sha256", contraseña.encode(), salt.encode(), iteraciones)
    return f"{salt}${clave.hex()}"


def verificar_contraseña(contraseña: str, almacenado: str) -> bool:
    """Verifica la contraseña contra el hash almacenado."""
    iteraciones = 100_000
    try:
        salt, clave = almacenado.split("$")
        clave_nueva = hashlib.pbkdf2_hmac("sha256", contraseña.encode(), salt.encode(), iteraciones)
        return clave_nueva.hex() == clave
    except Exception:
        return False


def generar_token() -> str:
    return str(uuid.uuid4())


def obtener_token_del_header(autorizacion: str = Header(...)) -> str:
    """
    Extrae el token del header Authorization: Bearer <token>.
    Lanza 401 si el formato es incorrecto.
    
    """
    if not autorizacion.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Se requiere Authorization: Bearer <token>")
    return autorizacion[7:]


def obtener_usuario_del_token(token: str, usuarios: dict) -> tuple[str, dict]:
    """
    Busca el usuario cuyo session_token coincida con el token dado.
    Devuelve (nombre_usuario, datos_usuario) o lanza 401.
    """
    for nombre_usuario, datos in usuarios.items():
        if datos.get("session_token") == token:
            return nombre_usuario, datos
    raise HTTPException(status_code=401, detail="Token inválido o sesión expirada.")


def requiere_admin(datos_usuario: dict):
    """Lanza 403 si el usuario no es administrador."""
    if datos_usuario.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador.")
