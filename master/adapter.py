"""
Adaptador de Cliente - Versión Jerárquica Global
--------------------------------------------------
Transforma las respuestas internas en formato limpio para el usuario.
Ahora trabaja con catálogo global y rutas jerárquicas.
"""


def adaptar_respuesta_carga(nombre_archivo: str, area: str, subarea: str,
                           nodos: list[str], votos: dict) -> dict:
    """Adaptar respuesta de carga de archivo clasificado automáticamente."""
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
    """Formatea el árbol de clasificación con estadísticas.

    Ahora con rutas del catálogo global: Tecnología, Ciencias, Otros
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
