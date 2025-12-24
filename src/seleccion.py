import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import openpyxl

def cargar_clasificacion():
    """
    Carga la clasificación de CVs desde el archivo JSON.
    """
    with open('output/clasificacion_cvs.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def calcular_puntaje(cv_areas, areas_definidas):
    """
    Calcula el puntaje de un CV según la cantidad de coincidencias con las áreas definidas.
    """
    puntaje = 0
    for area in cv_areas:
        if area in areas_definidas:
            puntaje += 1
    return puntaje

def seleccionar_mejores_candidatos():
    """
    Selecciona a los mejores candidatos por área, basándose en el puntaje calculado.
    """
    clasificacion = cargar_clasificacion()
    
    # Cargar las áreas definidas
    areas_definidas = []
    with open('rules/areas.json', 'r', encoding='utf-8') as file:
        areas_data = json.load(file)
        areas_definidas = [area['nombre_area'] for area in areas_data['areas']]

    mejores_candidatos = {}

    # Procesar cada CV clasificado
    for archivo, cv_areas in clasificacion.items():
        puntaje = calcular_puntaje(cv_areas, areas_definidas)
        
        # Asignar al área correspondiente
        for area in cv_areas:
            if area not in mejores_candidatos:
                mejores_candidatos[area] = []
            
            mejores_candidatos[area].append({
                "cv": archivo,
                "puntaje": puntaje
            })

    # Ordenar los candidatos por puntaje
    for area in mejores_candidatos:
        mejores_candidatos[area].sort(key=lambda x: x['puntaje'], reverse=True)

    return mejores_candidatos

def guardar_mejores_candidatos(mejores_candidatos, ruta_salida="output/mejores_candidatos.json"):
    """
    Guarda los mejores candidatos por área en un archivo JSON.
    """
    with open(ruta_salida, 'w', encoding='utf-8') as file:
        json.dump(mejores_candidatos, file, ensure_ascii=False, indent=4)

def generar_excel(mejores_candidatos, ruta_salida="output/mejores_candidatos.xlsx"):
    """
    Genera un archivo Excel con los mejores candidatos.
    """
    # Crear un libro de trabajo de Excel
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Mejores Candidatos"
    
    # Agregar encabezados
    hoja.append(["Área", "CV", "Puntaje"])

    # Agregar los candidatos al archivo Excel
    for area, candidatos in mejores_candidatos.items():
        for candidato in candidatos:
            hoja.append([area, candidato["cv"], candidato["puntaje"]])

    # Guardar el archivo Excel
    libro.save(ruta_salida)
    print(f"Archivo Excel guardado en {ruta_salida}")

def enviar_correo(destinatario, asunto, cuerpo, archivo_adjunto):
    """
    Función para enviar un correo electrónico con el archivo adjunto.
    """
    # Configuración del servidor SMTP (Gmail en este caso)
    servidor_smtp = "smtp.gmail.com"
    puerto_smtp = 587
    correo_remitente = "tu_email@gmail.com"  # Cambia con tu correo de Gmail
    contrasena_remitente = "tu_contrasena"  # Cambia con tu contraseña o app password

    # Crear el objeto de mensaje
    mensaje = MIMEMultipart()
    mensaje["From"] = correo_remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto

    # Agregar cuerpo del mensaje
    mensaje.attach(MIMEText(cuerpo, "plain"))

    # Adjuntar el archivo
    adjunto = MIMEBase("application", "octet-stream")
    with open(archivo_adjunto, "rb") as archivo:
        adjunto.set_payload(archivo.read())
    encoders.encode_base64(adjunto)
    adjunto.add_header("Content-Disposition", f"attachment; filename={archivo_adjunto}")
    mensaje.attach(adjunto)

    # Enviar el correo
    try:
        servidor = smtplib.SMTP(servidor_smtp, puerto_smtp)
        servidor.starttls()  # Establecer conexión segura
        servidor.login(correo_remitente, contrasena_remitente)
        texto = mensaje.as_string()
        servidor.sendmail(correo_remitente, destinatario, texto)
        servidor.quit()
        print(f"Correo enviado a {destinatario}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

def mostrar_mejores_candidatos():
    """
    Muestra los mejores candidatos por área, guarda el resultado en JSON y genera un archivo Excel.
    """
    mejores = seleccionar_mejores_candidatos()
    
    # Guardar los mejores candidatos en un archivo JSON
    guardar_mejores_candidatos(mejores)

    # Generar archivo Excel con los mejores candidatos
    generar_excel(mejores)

    # Mostrar los mejores candidatos en la consola
    for area, candidatos in mejores.items():
        print(f"\nÁrea: {area}")
        for candidato in candidatos:
            print(f"  - {candidato['cv']} con puntaje {candidato['puntaje']}")
    
    print("\nResultados guardados en 'output/mejores_candidatos.json' y 'output/mejores_candidatos.xlsx'.")

    # Enviar correo con los resultados adjuntos
    enviar_correo("destinatario@correo.com", 
                  "Resultados de Selección de Candidatos", 
                  "Adjunto los resultados de la selección de candidatos.", 
                  "output/mejores_candidatos.xlsx")

if __name__ == "__main__":
    mostrar_mejores_candidatos()
