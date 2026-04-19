"""
Adaptador de Cliente
--------------------
Transforma las respuestas internas en formato limpio para el usuario.
Soporta la jerarquía de dos niveles (temática → subtemática).
"""


def adaptar_respuesta_carga(nombre_archivo: str, area: str, subarea: str,
                           nodos: list[str], votos: dict) -> dict:
    ruta = f"{area}/{subarea}" if subarea else area
    return {
        "mensaje":      "Archivo procesado correctamente.",
        "archivo":      nombre_archivo,
        "clasificado_en": ruta,
        "area":         area,
        "subarea":      subarea or None,
        "replicado_en": nodos,
        "consenso": {
            "votos_por_nodo": votos,
            "resultado":      ruta
        }
    }


def adaptar_respuesta_archivos(nombre_usuario: str, arbol: dict) -> dict:
    """
    Formatea el árbol de dos niveles con estadísticas.

    arbol esperado:
    {
      "Redes": {
        "files":   ["paper1.pdf"],
        "Protocolos": {"files": ["paper2.pdf"]},
        "Topologías":  {"files": []}
      },
      "General": {"files": ["paper3.pdf"]}
    }
    """
    total = 0
    for datos_area in arbol.values():
        total += len(datos_area.get("files", []))
        for clave, valor in datos_area.items():
            if clave != "files" and isinstance(valor, dict):
                total += len(valor.get("files", []))

    return {
        "usuario":        nombre_usuario,
        "total_archivos": total,
        "clasificacion":  arbol
    }


def resolver_area(predicho: str, áreas_usuario: dict) -> tuple[str, str]:
    """
    Resuelve el área y subárea a partir de la predicción del clasificador
    y la jerarquía del usuario.

    áreas_usuario: {"Redes": ["Protocolos", "Topologías"], "General": []}

    Retorna (area, subarea). Si no hay match → ("General", "").
    """
    if predicho in áreas_usuario:
        return predicho, ""

    for area, subareas in áreas_usuario.items():
        if predicho in subareas:
            return area, predicho

    return "General", ""


def construir_áreas_planas(áreas_usuario: dict) -> list[str]:
    """Construye lista plana de todas las áreas y subáreas para el clasificador."""
    planas = list(áreas_usuario.keys())
    for subareas in áreas_usuario.values():
        planas.extend(subareas)
    return list(set(planas))
