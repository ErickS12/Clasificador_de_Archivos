"""
Consenso por Mayoría - Versión Jerárquica
========================================
El consenso por mayoría ahora trabaja con rutas jerárquicas completas.
Cada worker predice una ruta (ej: "Tecnología/Inteligencia Artificial").
El maestro recopila estas predicciones y determina cuál es la más común.

Si no hay consenso o los workers fallan, se asigna automáticamente "Otros/General".

El consenso por ahora ya esta implementado pero solo funciona en localhost. 

Para pasar a despliegue físico en LAN, reemplazar la lista WORKERS
con las IPs reales de cada laptop. Ejemplo:
    WORKERS = [
        "http://192.168.1.101:5001/process",   # laptop worker 1
        "http://192.168.1.102:5002/process",   # laptop worker 2
        "http://192.168.1.103:5003/process",   # laptop worker 3
    ]

Los workers se levantan con el comando: uvicorn worker.main:app --host --port 5001

"""

import requests
import json
from fastapi import HTTPException

# FASE 7: para que deje de funcionar en localhost, reemplazar las URLs por las IPs reales de cada laptop worker.
WORKERS = [
    "http://localhost:5001/process",
    "http://localhost:5002/process",
    "http://localhost:5003/process",
]



def enviar_a_worker(url_worker: str, ruta_pdf: str, categorias_global: list[str]) -> str | None:
    """Envía el PDF a un worker. Retorna la ruta predicha o None si falla.
    
    Args:
        url_worker - URL del endpoint /process del worker
        ruta_pdf - ruta al archivo PDF
        categorias_global - lista de todas las categorías disponibles
                           (ej: ["Tecnología/IA", "Ciencias/Biología", ...])
    
    Returns:
        Ruta predicha (ej: "Tecnología/Inteligencia Artificial") o None si falla
    """
    try:
        with open(ruta_pdf, "rb") as f:
            response = requests.post(
                url_worker,
                files={"archivo": f},
                data={"categorias_global": json.dumps(categorias_global)},
                timeout=10
            )
        return response.json()["area"]
    except Exception:
        return None


def clasificar_con_consenso(ruta_pdf: str, categorias_global: list[str]) -> tuple[str, dict]:
    """
    Clasifica el PDF usando consenso de mayoría entre los workers.
    Ahora con predicciones jerárquicas.

    Args:
        ruta_pdf - ruta al archivo PDF
        categorias_global - lista de rutas jerárquicas disponibles

    Returns:
        (ruta_ganadora, votos_por_nodo)
        
        Ejemplos:
            ("Tecnología/Inteligencia Artificial", {"node1": "Tecnología/IA", ...})
            ("Otros/General", {"node1": "sin respuesta", ...})  # fallback
    """
    votos      = {}
    resultados = []

    for i, url in enumerate(WORKERS):
        nodo = f"node{i + 1}"
        ruta = enviar_a_worker(url, ruta_pdf, categorias_global)
        if ruta is not None:
            votos[nodo] = ruta
            resultados.append(ruta)
            print(f"[CONSENSO] {nodo} → {ruta}")
        else:
            votos[nodo] = "sin respuesta"
            print(f"[CONSENSO] {nodo} no disponible")

    if not resultados:
        raise HTTPException(
            status_code=503,
            detail="Ningún worker disponible. Verifica que al menos uno esté corriendo."
        )

    ruta_final = max(set(resultados), key=resultados.count)
    print(f"[CONSENSO] resultado final: {ruta_final}")
    return ruta_final, votos
