"""
Configuración del clúster.

Permite usar localhost en desarrollo y URLs reales cuando el sistema se
despliega en varias computadoras.
"""

from __future__ import annotations

import json
import os
from typing import Any


DEFAULT_NODES = [
    {"id": 1, "url": "http://localhost:5001"},
    {"id": 2, "url": "http://localhost:5002"},
    {"id": 3, "url": "http://localhost:5003"},
    {"id": 4, "url": "http://localhost:8000"},
]


def obtener_nodos_cluster() -> list[dict[str, Any]]:
    """
    Devuelve la lista de nodos del clúster.

    Orden de prioridad:
      1. CLUSTER_NODES_JSON con una lista JSON de objetos {"id", "url"}
      2. CLUSTER_NODE_1_URL ... CLUSTER_NODE_4_URL
      3. valores por defecto en localhost
    """
    nodos_json = os.getenv("CLUSTER_NODES_JSON")
    if nodos_json:
        try:
            nodos = json.loads(nodos_json)
            if isinstance(nodos, list) and all(
                isinstance(nodo, dict) and "id" in nodo and "url" in nodo
                for nodo in nodos
            ):
                return sorted(nodos, key=lambda nodo: int(nodo["id"]))
        except Exception:
            pass

    nodos_configurados: list[dict[str, Any]] = []
    for nodo in DEFAULT_NODES:
        url_personalizada = os.getenv(f'CLUSTER_NODE_{nodo["id"]}_URL')
        nodos_configurados.append({
            "id": nodo["id"],
            "url": url_personalizada or nodo["url"],
        })

    return nodos_configurados


def obtener_url_nodo(nodo_id: int) -> str:
    """Devuelve la URL configurada para un nodo específico."""
    for nodo in obtener_nodos_cluster():
        if int(nodo["id"]) == nodo_id:
            return str(nodo["url"])
    raise ValueError(f"No existe configuración para el nodo {nodo_id}")
