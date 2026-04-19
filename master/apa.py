"""
Generador de Citas APA 7
=========================
ESTADO: 🔲 PENDIENTE — FASE 8

Extrae metadatos de los PDFs seleccionados y los formatea
en citas bibliográficas según la norma APA 7.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRATEGIA DE IMPLEMENTACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Los artículos científicos generalmente tienen en las
primeras páginas:
  - Título del artículo
  - Autores (nombre, apellido)
  - Año de publicación
  - Nombre de la revista/journal
  - Volumen, número, páginas
  - DOI (si aplica)

Opción A — Extracción con PyMuPDF (backend):
  1. Abrir el PDF del nodo
  2. Extraer texto de las primeras 2 páginas
  3. Usar regex para detectar patrones de autores, año, título
  4. Formatear en APA 7

Opción B — Procesamiento en el frontend con citation-js:
  1. El usuario sube o selecciona el PDF en el navegador
  2. citation-js extrae metadatos del archivo
  3. Se formatean directamente en el cliente
  4. Sin necesidad del endpoint POST /apa

Formato APA 7 esperado:
  Apellido, N., & Apellido2, N2. (Año). Título del artículo.
  Nombre de la Revista, Volumen(Número), páginas. https://doi.org/xxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
import fitz  # PyMuPDF


def extraer_metadatos_del_pdf(ruta_pdf: str) -> dict:
    """
    TODO FASE 8: Extraer metadatos bibliográficos de las primeras páginas del PDF.

    Retorna dict con:
    {
      "titulo":   str,
      "autores":  list[str],
      "año":      str,
      "revista":  str,
      "volumen":  str,
      "numero":   str,
      "paginas":  str,
      "doi":      str
    }
    """
    # TODO FASE 8: implementar extracción con regex sobre el texto de las primeras 2 páginas
    raise NotImplementedError("Implementar en Fase 8.")


def formatear_apa7(metadatos: dict) -> str:
    """
    TODO FASE 8: Formatear los metadatos extraídos en una cita APA 7.

    Ejemplo de salida:
    García, J., & López, M. (2023). Redes neuronales profundas para clasificación.
    Journal of Computer Science, 45(2), 123-145. https://doi.org/10.1234/jcs.2023

    Reglas APA 7 a considerar:
      - Hasta 20 autores: listar todos separados por ", &"
      - Más de 20: primeros 19 + "..." + último autor
      - Si no hay DOI: omitir esa parte
      - Si falta algún campo: omitir ese elemento de la cita
    """
    # TODO FASE 8: implementar
    raise NotImplementedError("Implementar en Fase 8.")


def generar_referencias_apa(rutas_pdf: list[str]) -> list[str]:
    """
    TODO FASE 8: Punto de entrada principal.
    Recibe lista de rutas a PDFs y devuelve lista de citas APA 7.

    Llamar desde el endpoint POST /apa en master/main.py.
    """
    # TODO FASE 8: implementar
    raise NotImplementedError("Implementar en Fase 8.")
