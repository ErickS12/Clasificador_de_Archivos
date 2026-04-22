"""
Módulos compartidos entre master y worker.
Contiene lógica de elección de líder y persistencia.
"""

from .election import (
    iniciar,
    obtener_url_lider,
    yo_soy_lider,
)

from .leader_db import (
    obtener_lider_actual,
    guardar_lider,
    actualizar_heartbeat,
)

__all__ = [
    "iniciar",
    "obtener_url_lider",
    "yo_soy_lider",
    "obtener_lider_actual",
    "guardar_lider",
    "actualizar_heartbeat",
]
