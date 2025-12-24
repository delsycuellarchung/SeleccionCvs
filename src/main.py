import sys
import os

# Añadir la carpeta 'src' al sys.path para que Python pueda importar correctamente desde 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import requests
from lector import leer_cvs
from clasificador import clasificar_cvs_por_area, guardar_clasificacion

RUTA_CVS = "data/cvs"
RUTA_SALIDA = "output/clasificacion_cvs.json"
URL_API_AREAS = "http://127.0.0.1:5000/ver_areas"

def obtener_areas():
    # Obtener las áreas desde el backend Flask
    response = requests.get(URL_API_AREAS)

    print(f"Status code: {response.status_code}")  # Imprimir el código de estado
    print(f"Response body: {response.text}")       # Imprimir la respuesta completa

    if response.status_code == 200:
        return response.json()["areas"]
    else:
        raise Exception("No se pudieron obtener las áreas desde el servidor.")

def main():
    try:
        # Obtener las áreas desde el servidor
        areas = obtener_areas()

        # Leer los CVs
        cvs = leer_cvs(RUTA_CVS)

        # Clasificar los CVs por las áreas obtenidas
        resultado = clasificar_cvs_por_area(cvs, areas)

        # Guardar el resultado de la clasificación
        guardar_clasificacion(resultado, RUTA_SALIDA)

        # Mostrar el resultado de la clasificación
        print("Clasificación final:\n")
        for archivo, areas in resultado.items():
            print(f"- {archivo} → {', '.join(areas)}")

        print("\nArchivo generado:", RUTA_SALIDA)

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
