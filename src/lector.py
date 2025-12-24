import os
import pdfplumber
from docx import Document


def leer_cvs(ruta_cvs):
    """
    Lee todos los CVs de una carpeta y devuelve una lista con:
    - nombre del archivo
    - texto limpio del CV
    """
    cvs = []

    if not os.path.exists(ruta_cvs):
        raise FileNotFoundError("La carpeta de CVs no existe.")

    archivos = os.listdir(ruta_cvs)

    if not archivos:
        raise ValueError("No hay CVs disponibles para procesar.")

    for archivo in archivos:
        ruta_archivo = os.path.join(ruta_cvs, archivo)
        texto = ""

        if archivo.lower().endswith(".pdf"):
            texto = leer_pdf(ruta_archivo)

        elif archivo.lower().endswith(".docx"):
            texto = leer_docx(ruta_archivo)

        else:
            continue  # Ignora otros formatos

        texto_limpio = limpiar_texto(texto)

        cvs.append({
            "archivo": archivo,
            "texto": texto_limpio
        })

    return cvs


def leer_pdf(ruta):
    texto = ""
    with pdfplumber.open(ruta) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() or ""
    return texto


def leer_docx(ruta):
    texto = ""
    doc = Document(ruta)
    for parrafo in doc.paragraphs:
        texto += parrafo.text + " "
    return texto


def limpiar_texto(texto):
    if not texto:
        return ""

    texto = texto.lower()
    texto = texto.replace("\n", " ")
    texto = texto.replace("\t", " ")
    texto = " ".join(texto.split())

    return texto
