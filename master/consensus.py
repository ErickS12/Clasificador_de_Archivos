"""
Consenso por Mayoría
El consenso por mayoría es un método de clasificación que se basa en la idea de que la decisión final se toma en función de la opción que reciba más votos. En este caso, cada worker procesa el PDF y devuelve un área predicha. El master recopila estas predicciones y determina cuál es la más común entre ellas.


El concenso por ahora ya esta implementado pero solo funciona en localhost. 

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



def enviar_a_worker(url_worker: str, ruta_pdf: str, areas_planas: list[str]) -> str | None:
    """Envía el PDF a un worker. Retorna el área predicha o None si falla."""
    try:
        with open(ruta_pdf, "rb") as f:
            response = requests.post(
                url_worker,
                files={"archivo": f},
                data={"areas_usuario": json.dumps(areas_planas)},
                timeout=10
            )
        return response.json()["area"]
    except Exception:
        return None


def clasificar_con_consenso(ruta_pdf: str, areas_planas: list[str]) -> tuple[str, dict]:
    """
    Clasifica el PDF usando consenso de mayoría entre los workers.

    Retorna:
        (área_ganadora, votos_por_nodo)
    """
    votos      = {}
    resultados = []

    for i, url in enumerate(WORKERS):
        nodo = f"node{i + 1}"
        area = enviar_a_worker(url, ruta_pdf, areas_planas)
        if area is not None:
            votos[nodo] = area
            resultados.append(area)
            print(f"[CONSENSO] {nodo} → {area}")
        else:
            votos[nodo] = "sin respuesta"
            print(f"[CONSENSO] {nodo} no disponible")

    if not resultados:
        raise HTTPException(
            status_code=503,
            detail="Ningún worker disponible. Verifica que al menos uno esté corriendo."
        )

    area_final = max(set(resultados), key=resultados.count)
    print(f"[CONSENSO] resultado final: {area_final}")
    return area_final, votos
