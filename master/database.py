"""
Gestor de Base de Datos — Supabase / PostgreSQL
================================================
ESTADO: 🔲 PENDIENTE — FASE 4

Este módulo reemplazará el sistema de archivos JSON por Supabase
como gestor de metadatos y autenticación.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASOS PARA IMPLEMENTAR (Fase 4):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Crear proyecto en https://supabase.com
2. Instalar cliente:
       pip install supabase

3. Crear las siguientes tablas en Supabase (SQL Editor):

    -- Tabla de usuarios
    CREATE TABLE usuarios (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        session_token TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- Tabla de temáticas (2 niveles: parent_id NULL = nivel 1)
    CREATE TABLE tematicas (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        nombre TEXT NOT NULL,
        nivel INT NOT NULL CHECK (nivel IN (1, 2)),
        parent_id UUID REFERENCES tematicas(id) ON DELETE CASCADE,
        user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- Tabla de documentos
    CREATE TABLE documentos (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        nombre TEXT NOT NULL,
        tematica_id UUID REFERENCES tematicas(id) ON DELETE CASCADE,
        user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
        nodos JSONB,
        votos JSONB,
        version INT DEFAULT 1,
        created_at TIMESTAMPTZ DEFAULT now()
    );

4. Copiar la URL y la clave anon de Supabase y definirlas como
   variables de entorno (ver .env.example).

5. Reemplazar las funciones de este módulo en main.py:
   - load_users()      → get_user_by_username()
   - save_users()      → upsert_user()
   - load_metadata()   → get_documents_by_user()
   - save_metadata()   → insert_document()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# TODO FASE 4: descomentar cuando instales supabase
# from supabase import create_client, Client
# import os
#
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Stubs que serán reemplazados en Fase 4 ───────────────────────

def obtener_usuario_por_nombre(nombre_usuario: str) -> dict | None:
    """
    TODO FASE 4: Consultar tabla 'usuarios' por nombre_usuario.
    Por ahora no hace nada — la lógica está en main.py con JSON.
    """
    raise NotImplementedError("Implementar en Fase 4 con Supabase.")


def insertar_o_actualizar_usuario(datos_usuario: dict):
    """
    TODO FASE 4: Insertar o actualizar usuario en Supabase.
    """
    raise NotImplementedError("Implementar en Fase 4 con Supabase.")


def obtener_documentos_por_usuario(id_usuario: str) -> list[dict]:
    """
    TODO FASE 4: Consultar todos los documentos de un usuario.
    """
    raise NotImplementedError("Implementar en Fase 4 con Supabase.")


def insertar_documento(datos_doc: dict):
    """
    TODO FASE 4: Insertar registro de documento en Supabase.
    """
    raise NotImplementedError("Implementar en Fase 4 con Supabase.")


def eliminar_registro_documento(id_doc: str):
    """
    TODO FASE 4: Eliminar registro de documento.
    ON DELETE CASCADE eliminará referencias en subtemáticas automáticamente.
    """
    raise NotImplementedError("Implementar en Fase 4 con Supabase.")


def obtener_documentos_en_tema(id_tema: str) -> list[dict]:
    """
    TODO FASE 4: Obtener todos los documentos de una temática
    (incluyendo subtemáticas) para el borrado en 2 pasos.
    """
    raise NotImplementedError("Implementar en Fase 4 con Supabase.")


def eliminar_tema_cascada(id_tema: str):
    """
    TODO FASE 5: Eliminar temática con ON DELETE CASCADE.
    Borra subtemáticas y registros de documentos automáticamente.
    Llamar SOLO después de que el borrado físico fue confirmado por los workers.
    """
    raise NotImplementedError("Implementar en Fase 5 con Supabase CASCADE.")
