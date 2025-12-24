import json
import os


def cargar_areas():
    """
    Lee el archivo 'areas.json' y devuelve las áreas definidas.
    """
    AREAS_JSON_PATH = "rules/areas.json"

    if os.path.exists(AREAS_JSON_PATH):
        with open(AREAS_JSON_PATH, "r", encoding="utf-8") as file:
            return json.load(file)["areas"]
    else:
        raise FileNotFoundError(f"El archivo {AREAS_JSON_PATH} no existe.")


def clasificar_cvs_por_area(cvs, areas):
    """
    Clasifica los CVs por las áreas definidas en 'areas.json'.

    :param cvs: lista de diccionarios con {archivo, texto}
    :param areas: lista de áreas con palabras clave para clasificación
    :return: diccionario con {archivo: [áreas]}
    """
    resultado = {}

    for cv in cvs:
        archivo = cv["archivo"]
        texto = cv["texto"]

        areas_encontradas = []

        # Comparar con las palabras clave de cada área
        for area in areas:
            nombre_area = area["nombre_area"]
            palabras_clave = area["palabras_clave"]

            for palabra in palabras_clave:
                if palabra in texto:
                    areas_encontradas.append(nombre_area)
                    break  # Detener la búsqueda si ya se encuentra una coincidencia

        if not areas_encontradas:
            areas_encontradas = ["No clasificado"]

        resultado[archivo] = areas_encontradas

    return resultado



def guardar_clasificacion(resultado, ruta_salida):
    """
    Guarda la clasificación en un archivo JSON
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)
