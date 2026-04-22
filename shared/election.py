"""
Elección de Líder — Algoritmo Bully
=====================================
Permite que cualquier nodo tome el rol de maestro cuando el líder actual cae.

CÓMO FUNCIONA:
  1. Al arrancar, cada nodo consulta Supabase para ver quién es el líder actual.
  2. Un hilo de heartbeat pinga al líder cada N segundos.
  3. Si el líder no responde tras MAX_INTENTOS, se dispara una elección.
  4. Algoritmo Bully: el nodo con ID más alto que esté disponible gana.
  5. El ganador escribe su URL en Supabase y avisa a todos los demás.

CONFIGURACIÓN (Fase 7 — reemplazar con IPs reales de la LAN):
  Asignar un ID único a cada laptop. El ID más alto tiene mayor prioridad.
  Ejemplo:
    Laptop A (maestro original) → ID 4  ← mayor prioridad
    Laptop B (worker 1)         → ID 3
    Laptop C (worker 2)         → ID 2
    Laptop D (worker 3)         → ID 1  ← menor prioridad
"""

import os
import time
import threading
import requests
from .leader_db import (
    obtener_lider_actual,
    guardar_lider,
    actualizar_heartbeat,
)

# ── Configuración de nodos ──────────────────────────────────────────────────
# TODO FASE 7: reemplazar con IPs reales de la LAN
NODOS = [
    {"id": 1, "url": "http://localhost:5001"},
    {"id": 2, "url": "http://localhost:5002"},
    {"id": 3, "url": "http://localhost:5003"},
    {"id": 4, "url": "http://localhost:8000"},
]

# ID de ESTE nodo — configurar por variable de entorno en cada laptop
# Ejemplo en terminal: export NODO_ID=3
MI_ID: int   = int(os.getenv("NODO_ID", "4"))
MI_URL: str  = next(n["url"] for n in NODOS if n["id"] == MI_ID)

# Parámetros de heartbeat
INTERVALO_HEARTBEAT_SEG = 5    # cada cuántos segundos ping al líder
MAX_INTENTOS_FALLIDOS   = 3    # intentos antes de declarar líder caído
TIMEOUT_REQUEST_SEG     = 2    # timeout por petición HTTP

# Estado global del módulo
_lider_url: str | None    = None
_yo_soy_lider: bool       = False
_lock                     = threading.Lock()
_eleccion_en_curso: bool  = False


# ── API pública ─────────────────────────────────────────────────────────────

def iniciar(app):
    """
    Punto de entrada. Llamar desde el evento startup de FastAPI.
    Registra los endpoints de elección en la app y arranca el heartbeat.
    
    Uso en main.py:
        from shared.election import iniciar as iniciar_eleccion
        
        @app.on_event("startup")
        async def evento_inicio():
            iniciar_eleccion(app)
    """
    _registrar_endpoints(app)
    _unirse_al_cluster()
    hilo = threading.Thread(target=_loop_heartbeat, daemon=True)
    hilo.start()
    print(f"[ELECTION] Nodo {MI_ID} iniciado. URL: {MI_URL}")


def obtener_url_lider() -> str | None:
    """Retorna la URL del líder actual. Usar en consensus.py y master/main.py."""
    with _lock:
        return _lider_url


def yo_soy_lider() -> bool:
    """True si ESTE nodo es el líder activo."""
    with _lock:
        return _yo_soy_lider


# ── Lógica interna ──────────────────────────────────────────────────────────

def _unirse_al_cluster():
    """Al arrancar, ver quién es el líder actual en Supabase."""
    global _lider_url, _yo_soy_lider
    lider = obtener_lider_actual()
    if lider:
        with _lock:
            _lider_url    = lider["nodo_url"]
            _yo_soy_lider = (lider["nodo_id"] == MI_ID)
        print(f"[ELECTION] Líder actual: Nodo {lider['nodo_id']} ({_lider_url})")
    else:
        print("[ELECTION] Sin líder registrado. Iniciando elección...")
        _iniciar_eleccion()


def _loop_heartbeat():
    """Hilo que corre indefinidamente comprobando si el líder sigue vivo."""
    fallos = 0
    while True:
        time.sleep(INTERVALO_HEARTBEAT_SEG)

        with _lock:
            soy_lider = _yo_soy_lider
            url_lider = _lider_url

        if soy_lider:
            # Si soy el líder, actualizo mi propio heartbeat en Supabase
            actualizar_heartbeat(MI_ID)
            fallos = 0
            continue

        if not url_lider:
            _iniciar_eleccion()
            continue

        # Ping al líder
        if _ping(url_lider):
            fallos = 0
        else:
            fallos += 1
            print(f"[ELECTION] Líder no responde ({fallos}/{MAX_INTENTOS_FALLIDOS})")
            if fallos >= MAX_INTENTOS_FALLIDOS:
                print("[ELECTION] Líder caído. Iniciando elección...")
                fallos = 0
                _iniciar_eleccion()


def _iniciar_eleccion():
    """Algoritmo Bully: avisa a nodos con ID mayor. Si nadie responde, gano."""
    global _eleccion_en_curso
    with _lock:
        if _eleccion_en_curso:
            return
        _eleccion_en_curso = True

    try:
        nodos_mayores = [n for n in NODOS if n["id"] > MI_ID]
        alguno_respondio = False

        for nodo in nodos_mayores:
            try:
                r = requests.post(
                    f"{nodo['url']}/election/start",
                    json={"candidato_id": MI_ID},
                    timeout=TIMEOUT_REQUEST_SEG,
                )
                if r.status_code == 200:
                    alguno_respondio = True
                    print(f"[ELECTION] Nodo {nodo['id']} respondió — él tomará el liderazgo")
                    break
            except Exception:
                pass

        if not alguno_respondio:
            # Nadie con ID mayor respondió → yo gano
            _proclamarme_lider()
    finally:
        with _lock:
            _eleccion_en_curso = False


def _proclamarme_lider():
    """Me declaro líder, guardo en Supabase y aviso a todos."""
    global _lider_url, _yo_soy_lider
    guardar_lider({"nodo_id": MI_ID, "nodo_url": MI_URL})

    with _lock:
        _lider_url    = MI_URL
        _yo_soy_lider = True

    print(f"[ELECTION] ✅ Nodo {MI_ID} es el nuevo líder.")

    # Avisar a todos los demás
    for nodo in NODOS:
        if nodo["id"] == MI_ID:
            continue
        try:
            requests.post(
                f"{nodo['url']}/election/coordinator",
                json={"lider_id": MI_ID, "lider_url": MI_URL},
                timeout=TIMEOUT_REQUEST_SEG,
            )
        except Exception:
            pass


def _ping(url: str) -> bool:
    """Retorna True si el nodo en url responde al heartbeat."""
    try:
        r = requests.get(f"{url}/heartbeat", timeout=TIMEOUT_REQUEST_SEG)
        return r.status_code == 200
    except Exception:
        return False


# ── Endpoints que se inyectan en la app FastAPI ─────────────────────────────

def _registrar_endpoints(app):
    """
    Registra los 3 endpoints necesarios para el protocolo de elección.
    Se llaman entre nodos — no son endpoints del cliente.
    """
    from fastapi import Request

    @app.get("/heartbeat")
    def heartbeat():
        """Responde para confirmar que este nodo está vivo."""
        return {"nodo_id": MI_ID, "lider": yo_soy_lider()}

    @app.post("/election/start")
    async def recibir_eleccion(request: Request):
        """
        Otro nodo nos avisa que inició una elección.
        Si nuestro ID es mayor, respondemos y disparamos nuestra propia elección.
        """
        data = await request.json()
        candidato_id = data.get("candidato_id", 0)
        if MI_ID > candidato_id:
            # Arrancamos nuestra propia elección en segundo plano
            hilo = threading.Thread(target=_iniciar_eleccion, daemon=True)
            hilo.start()
            return {"status": "ok", "nodo_id": MI_ID}
        return {"status": "ignorado"}

    @app.post("/election/coordinator")
    async def recibir_coordinador(request: Request):
        """El nuevo líder nos avisa quién ganó la elección."""
        global _lider_url, _yo_soy_lider
        data = await request.json()
        lider_id  = data.get("lider_id")
        lider_url = data.get("lider_url")
        with _lock:
            _lider_url    = lider_url
            _yo_soy_lider = (lider_id == MI_ID)
        print(f"[ELECTION] Nuevo líder confirmado: Nodo {lider_id} ({lider_url})")
        return {"status": "ok"}

    @app.get("/leader")
    def obtener_lider():
        """Endpoint público para que el frontend sepa a quién hablarle."""
        url = obtener_url_lider()
        if not url:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Sin líder disponible.")
        return {"lider_url": url}
