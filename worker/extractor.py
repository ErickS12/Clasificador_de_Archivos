import fitz  # PyMuPDF


def extraer_texto(ruta_pdf: str) -> str:
    doc  = fitz.open(ruta_pdf)
    texto = ""
    for page in doc:
        texto += page.get_text()
    return texto
