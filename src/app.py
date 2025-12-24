from flask import Flask, render_template, request, jsonify
import json
import os
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración para el directorio donde se guardarán los CVs subidos
UPLOAD_FOLDER = 'uploads/cvs'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Función para verificar si el archivo tiene extensión PDF
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta para recibir y clasificar un nuevo CV
@app.route('/subir_cv', methods=['POST'])
def subir_cv():
    if 'cv_file' not in request.files:
        return jsonify({"error": "No se proporcionó un archivo"}), 400
    
    file = request.files['cv_file']
    
    if file.filename == '':
        return jsonify({"error": "No se seleccionó un archivo"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extraer el texto del CV PDF
        text = extract_text_from_pdf(filepath)
        
        # Clasificar el CV automáticamente según las palabras clave
        areas_clasificadas = classify_cv(text)

        # Guardar la clasificación en el archivo JSON
        save_cv_classification(filename, areas_clasificadas)

        return jsonify({"message": "CV subido y clasificado correctamente", "areas": areas_clasificadas}), 200
    
    return jsonify({"error": "Formato de archivo no permitido"}), 400

# Función para extraer texto de un archivo PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        text = ""
        for page_num in range(reader.numPages):
            text += reader.getPage(page_num).extract_text()
        return text

# Función para clasificar un CV basándose en las áreas definidas
def classify_cv(text):
    with open('rules/areas.json', 'r', encoding='utf-8') as file:
        areas_data = json.load(file)
    
    areas_clasificadas = []
    for area in areas_data['areas']:
        for keyword in area['palabras_clave']:
            if keyword.lower() in text.lower():
                areas_clasificadas.append(area['nombre_area'])
                break

    return areas_clasificadas

# Función para guardar la clasificación del CV
def save_cv_classification(cv_filename, areas):
    classification = {}
    
    # Cargar la clasificación actual
    if os.path.exists('output/clasificacion_cvs.json'):
        with open('output/clasificacion_cvs.json', 'r', encoding='utf-8') as file:
            classification = json.load(file)
    
    # Agregar la clasificación del nuevo CV
    classification[cv_filename] = areas

    # Guardar la clasificación actualizada
    with open('output/clasificacion_cvs.json', 'w', encoding='utf-8') as file:
        json.dump(classification, file, ensure_ascii=False, indent=4)

# Página principal (Dashboard)
@app.route('/')
def dashboard():
    return render_template('index.html')

# Ruta para cargar la clasificación de CVs
@app.route('/ver_cvs', methods=['GET'])
def ver_cvs():
    try:
        # Cargar la clasificación desde el archivo JSON
        with open('output/clasificacion_cvs.json', 'r', encoding='utf-8') as file:
            clasificacion = json.load(file)
        return jsonify(clasificacion)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Ruta para cargar los puestos disponibles
@app.route('/ver_puestos', methods=['GET'])
def ver_puestos():
    try:
        # Cargar los puestos desde el archivo JSON
        with open('puestos.json', 'r', encoding='utf-8') as file:
            puestos = json.load(file)
        return jsonify(puestos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para agregar un puesto disponible
@app.route('/agregar_puesto', methods=['POST'])
def agregar_puesto():
    data = request.get_json()
    try:
        # Obtener los datos del puesto
        nombre_puesto = data['nombre_puesto']
        area_puesto = data['area_puesto']
        formacion_academica = data['formacion_academica']
        experiencia_laboral = data['experiencia_laboral']
        habilidades = data['habilidades']
        certificaciones = data['certificaciones']
        
        # Guardar el nuevo puesto en el archivo JSON
        puesto = {
            "nombre_puesto": nombre_puesto,
            "area_puesto": area_puesto,
            "formacion_academica": formacion_academica,
            "experiencia_laboral": experiencia_laboral,
            "habilidades": habilidades,
            "certificaciones": certificaciones
        }

        # Aquí se guardan en puestos.json
        with open('puestos.json', 'r+') as file:
            puestos = json.load(file)
            puestos.append(puesto)
            file.seek(0)
            json.dump(puestos, file, ensure_ascii=False, indent=4)
        
        return jsonify({"message": "Puesto agregado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
