from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import json
import os
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Servir la carpeta `img` que está en la raíz del proyecto (fuera de `src`) en la URL /img/<file>
@app.route('/img/<path:filename>')
def serve_root_img(filename):
    # app.root_path apunta a la carpeta `src`; la carpeta `img` está en el directorio padre
    img_folder = os.path.abspath(os.path.join(app.root_path, '..', 'img'))
    return send_from_directory(img_folder, filename)

# Configuración para el directorio donde se guardarán los CVs subidos
UPLOAD_FOLDER = 'uploads/cvs'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta para descargar un CV guardado
@app.route('/download_cv/<path:filename>')
def download_cv(filename):
    try:
        # serve from the configured upload folder
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

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

# Ruta para agregar un nuevo puesto disponible
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

        # Guardar en puestos.json (crear si no existe, y escribir de forma segura)
        puestos_file = 'puestos.json'
        if os.path.exists(puestos_file):
            with open(puestos_file, 'r', encoding='utf-8') as f:
                try:
                    puestos = json.load(f)
                except json.JSONDecodeError:
                    puestos = []
        else:
            puestos = []

        puestos.append(puesto)

        # Escribir reemplazando el contenido (modo seguro)
        with open(puestos_file, 'w', encoding='utf-8') as f:
            json.dump(puestos, f, ensure_ascii=False, indent=4)
        
        return jsonify({"message": "Puesto agregado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Ruta para cargar los puestos disponibles
@app.route('/ver_puestos', methods=['GET'])
def ver_puestos():
    try:
        # Cargar los puestos desde el archivo JSON (si no existe, devolver lista vacía)
        puestos_file = 'puestos.json'
        if not os.path.exists(puestos_file):
            return jsonify([])

        with open(puestos_file, 'r', encoding='utf-8') as file:
            try:
                puestos = json.load(file)
            except json.JSONDecodeError:
                puestos = []
        return jsonify(puestos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para editar un puesto existente
@app.route('/editar_puesto', methods=['POST'])
def editar_puesto():
    data = request.get_json()
    puesto_nombre = data['nombre_puesto']
    
    # Cargar puestos desde el archivo JSON
    with open('puestos.json', 'r+', encoding='utf-8') as file:
        puestos = json.load(file)
        
        # Buscar y editar el puesto
        for puesto in puestos:
            if puesto['nombre_puesto'] == puesto_nombre:
                puesto['area_puesto'] = data['area_puesto']
                puesto['formacion_academica'] = data['formacion_academica']
                puesto['experiencia_laboral'] = data['experiencia_laboral']
                puesto['habilidades'] = data['habilidades']
                puesto['certificaciones'] = data['certificaciones']
                break
        
        file.seek(0)
        json.dump(puestos, file, ensure_ascii=False, indent=4)
    
    return jsonify({"message": "Puesto editado correctamente"}), 200

# Ruta para eliminar un puesto
@app.route('/eliminar_puesto', methods=['POST'])
def eliminar_puesto():
    data = request.get_json()
    puesto_nombre = data['nombre_puesto']
    
    # Cargar puestos desde el archivo JSON
    with open('puestos.json', 'r+', encoding='utf-8') as file:
        puestos = json.load(file)
        
        # Buscar y eliminar el puesto
        puestos = [puesto for puesto in puestos if puesto['nombre_puesto'] != puesto_nombre]
        
        file.seek(0)
        json.dump(puestos, file, ensure_ascii=False, indent=4)
    
    return jsonify({"message": "Puesto eliminado correctamente"}), 200

# Página principal (Dashboard)
@app.route('/')
def dashboard():
    return render_template('index.html')


@app.route('/puestos')
def puestos_view():
    return render_template('puestos.html')


@app.route('/candidatos')
def candidatos_view():
    return render_template('candidatos.html')


# Página: Base de Talentos (lista completa desde Excel/CSV existente)
@app.route('/base_talentos')
def base_talentos_view():
    return render_template('base_talentos.html')


# API: devuelve filas del Excel/CSV existente como JSON
@app.route('/api/base_talentos', methods=['GET'])
def api_base_talentos():
    # Prioridad: output/mejores_candidatos.xlsx, luego output/ranking.csv, luego output/clasificacion_cvs.json
    import csv
    from flask import send_file
    xlsx_path = os.path.join('output', 'mejores_candidatos.xlsx')
    csv_path = os.path.join('output', 'ranking.csv')
    json_path = os.path.join('output', 'clasificacion_cvs.json')

    # Try Excel first
    if os.path.exists(xlsx_path):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(xlsx_path, data_only=True)
            ws = wb.active
            rows = list(ws.values)
            if not rows:
                return jsonify([])
            headers = [str(h) if h is not None else '' for h in rows[0]]
            out = []
            for r in rows[1:]:
                obj = {}
                for i, v in enumerate(r):
                    key = headers[i] if i < len(headers) else f'col_{i}'
                    obj[key] = v
                out.append(obj)
            return jsonify(out)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Then CSV
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return jsonify(list(reader))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Fallback to clasificacion JSON -> convert to rows (filename + areas)
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            out = []
            for filename, areas in (data or {}).items():
                out.append({'archivo': filename, 'areas': areas})
            return jsonify(out)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify([])


# Endpoint para descargar el Excel/CSV original (si existe)
@app.route('/download/base_talentos')
def download_base_talentos():
    # prefer xlsx then csv then json
    xlsx_path = os.path.abspath(os.path.join('output', 'mejores_candidatos.xlsx'))
    csv_path = os.path.abspath(os.path.join('output', 'ranking.csv'))
    json_path = os.path.abspath(os.path.join('output', 'clasificacion_cvs.json'))
    if os.path.exists(xlsx_path):
        return send_file(xlsx_path, as_attachment=True)
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True)
    if os.path.exists(json_path):
        return send_file(json_path, as_attachment=True)
    return jsonify({'error': 'No hay archivo disponible para descargar'}), 404

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


# Plantillas de cargo (UI)
@app.route('/plantillas')
def plantillas_view():
    return render_template('plantillas.html')


# Página: Selección por Puesto
@app.route('/seleccion')
def seleccion_view():
    return render_template('seleccion.html')


# API: puestos abiertos
@app.route('/api/puestos_abiertos', methods=['GET'])
def api_puestos_abiertos():
    puestos_file = 'puestos.json'
    if not os.path.exists(puestos_file):
        return jsonify([])
    with open(puestos_file, 'r', encoding='utf-8') as f:
        try:
            puestos = json.load(f)
        except json.JSONDecodeError:
            puestos = []
    # consider puesto open if 'estado' != 'cerrado' (default: abierto)
    abiertos = []
    for p in puestos:
        if str(p.get('estado','abierto')).lower() != 'cerrado':
            abiertos.append(p)
    return jsonify(abiertos)


# API: seleccionar candidato final para un puesto (cierra el puesto)
@app.route('/api/seleccionar_final', methods=['POST'])
def api_seleccionar_final():
    try:
        payload = request.get_json()
        puesto_nombre = payload.get('puesto_nombre')
        candidato = payload.get('candidato')
        if not puesto_nombre or not candidato:
            return jsonify({'error':'Faltan datos'}), 400

        puestos_file = 'puestos.json'
        if not os.path.exists(puestos_file):
            return jsonify({'error':'No hay puestos registrados'}), 400

        with open(puestos_file, 'r+', encoding='utf-8') as f:
            try:
                puestos = json.load(f)
            except json.JSONDecodeError:
                puestos = []

            found = False
            for puesto in puestos:
                if puesto.get('nombre_puesto') == puesto_nombre:
                    puesto['estado'] = 'cerrado'
                    puesto['seleccionado'] = {
                        'candidato': candidato,
                        'selected_at': str(__import__('datetime').datetime.utcnow())
                    }
                    found = True
                    break

            if not found:
                return jsonify({'error':'Puesto no encontrado'}), 404

            f.seek(0)
            f.truncate()
            json.dump(puestos, f, ensure_ascii=False, indent=4)

        # also append to output/selecciones.json for record keeping
        sel_file = os.path.join('output','selecciones.json')
        os.makedirs('output', exist_ok=True)
        try:
            if os.path.exists(sel_file):
                with open(sel_file,'r',encoding='utf-8') as sf:
                    selecciones = json.load(sf)
            else:
                selecciones = []
        except json.JSONDecodeError:
            selecciones = []

        selecciones.append({'puesto': puesto_nombre, 'candidato': candidato, 'at': str(__import__('datetime').datetime.utcnow())})
        with open(sel_file,'w',encoding='utf-8') as sf:
            json.dump(selecciones, sf, ensure_ascii=False, indent=4)

        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Página: Historial de Selecciones (solo lectura)
@app.route('/historial')
def historial_view():
    return render_template('historial.html')


# API: obtener historial de selecciones (con filtros opcionales)
@app.route('/api/selecciones', methods=['GET'])
def api_get_selecciones():
    sel_file = os.path.join('output','selecciones.json')
    if not os.path.exists(sel_file):
        return jsonify([])
    try:
        with open(sel_file,'r',encoding='utf-8') as f:
            try:
                selecciones = json.load(f)
            except json.JSONDecodeError:
                selecciones = []
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Load puestos and classifications to enrich records
    puestos = []
    if os.path.exists('puestos.json'):
        try:
            with open('puestos.json','r',encoding='utf-8') as pf:
                puestos = json.load(pf)
        except Exception:
            puestos = []

    clasif = {}
    if os.path.exists(os.path.join('output','clasificacion_cvs.json')):
        try:
            with open(os.path.join('output','clasificacion_cvs.json'),'r',encoding='utf-8') as cf:
                clasif = json.load(cf)
        except Exception:
            clasif = {}

    # Build enriched list
    enriched = []
    for s in selecciones:
        puesto_name = s.get('puesto')
        candidato = s.get('candidato')
        at = s.get('at') or s.get('fecha') or s.get('time')
        # find puesto details
        puesto_obj = next((p for p in puestos if p.get('nombre_puesto') == puesto_name), {})
        area = puesto_obj.get('area_puesto') or puesto_obj.get('area') or ''
        # get candidate score if available
        score = None
        raw = clasif.get(candidato)
        if isinstance(raw, dict) and isinstance(raw.get('score'), (int,float)):
            score = raw.get('score')
        # else try to infer numeric by length of areas
        elif isinstance(raw, list):
            score = len(raw)
        elif isinstance(raw, dict) and isinstance(raw.get('areas'), list):
            score = len(raw.get('areas'))

        enriched.append({
            'puesto': puesto_name,
            'area': area,
            'candidato': candidato,
            'score': score,
            'at': at,
            'raw': s
        })

    # Optional filtering via query params
    area_q = request.args.get('area')
    puesto_q = request.args.get('puesto')
    start_q = request.args.get('start')
    end_q = request.args.get('end')

    def parse_dt(v):
        if not v: return None
        try:
            # accept ISO or default str(datetime)
            return __import__('datetime').datetime.fromisoformat(v)
        except Exception:
            try:
                return __import__('datetime').datetime.fromisoformat(v.replace(' ', 'T'))
            except Exception:
                try:
                    return __import__('datetime').datetime.strptime(v, '%Y-%m-%d %H:%M:%S.%f')
                except Exception:
                    try:
                        return __import__('datetime').datetime.strptime(v, '%Y-%m-%d')
                    except Exception:
                        return None

    s_dt = parse_dt(start_q)
    e_dt = parse_dt(end_q)

    def in_range(item_at):
        if not item_at: return True
        dt = parse_dt(item_at)
        if not dt: return True
        if s_dt and dt < s_dt: return False
        if e_dt and dt > e_dt: return False
        return True

    final = []
    for item in enriched:
        if area_q and area_q != item.get('area'): continue
        if puesto_q and puesto_q != item.get('puesto'): continue
        if not in_range(item.get('at')): continue
        final.append(item)

    # sort by date desc
    try:
        final.sort(key=lambda x: parse_dt(x.get('at')) or __import__('datetime').datetime.min, reverse=True)
    except Exception:
        pass

    return jsonify(final)


# API: entrevistas CRUD (stored in output/entrevistas.json)
@app.route('/api/entrevistas', methods=['GET'])
def api_get_entrevistas():
    file_path = os.path.join('output','entrevistas.json')
    if not os.path.exists(file_path):
        return jsonify([])
    try:
        with open(file_path,'r',encoding='utf-8') as f:
            try:
                items = json.load(f)
            except json.JSONDecodeError:
                items = []
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # optional filters
    puesto = request.args.get('puesto')
    candidato = request.args.get('candidato')
    estado = request.args.get('estado')

    out = []
    for it in items:
        if puesto and it.get('puesto') != puesto: continue
        if candidato and it.get('candidato') != candidato: continue
        if estado and it.get('estado') != estado: continue
        out.append(it)

    # sort chronologically by fecha (if present)
    def parse_dt(s):
        try:
            return __import__('datetime').datetime.fromisoformat(s)
        except Exception:
            return __import__('datetime').datetime.min

    out.sort(key=lambda x: parse_dt(x.get('fecha') or ''), reverse=False)
    return jsonify(out)


@app.route('/api/entrevistas', methods=['POST'])
def api_create_entrevista():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({'error':'no data'}), 400
        # required fields: puesto, candidato, fecha (ISO), tipo, medio
        required = ['puesto','candidato','fecha','tipo','medio']
        for k in required:
            if not payload.get(k):
                return jsonify({'error': f'Campo requerido: {k}'}), 400

        file_path = os.path.join('output','entrevistas.json')
        if os.path.exists(file_path):
            with open(file_path,'r',encoding='utf-8') as f:
                try:
                    arr = json.load(f)
                except json.JSONDecodeError:
                    arr = []
        else:
            arr = []

        import uuid
        item = {
            'id': str(uuid.uuid4()),
            'puesto': payload.get('puesto'),
            'candidato': payload.get('candidato'),
            'fecha': payload.get('fecha'),
            'tipo': payload.get('tipo'),
            'medio': payload.get('medio'),
            'observaciones': payload.get('observaciones',''),
            'estado': payload.get('estado','programada'),
            'created_at': str(__import__('datetime').datetime.utcnow()),
            'updated_at': None
        }
        arr.append(item)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path,'w',encoding='utf-8') as f:
            json.dump(arr, f, ensure_ascii=False, indent=4)
        return jsonify({'ok':True,'id': item['id']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/entrevistas/<eid>', methods=['PUT'])
def api_update_entrevista(eid):
    try:
        payload = request.get_json()
        file_path = os.path.join('output','entrevistas.json')
        if not os.path.exists(file_path):
            return jsonify({'error':'not found'}), 404
        with open(file_path,'r+',encoding='utf-8') as f:
            try:
                arr = json.load(f)
            except json.JSONDecodeError:
                arr = []
            updated = False
            for it in arr:
                if it.get('id') == eid:
                    # only allow updating entrevista fields (fecha,tipo,medio,observaciones,estado)
                    for k in ['fecha','tipo','medio','observaciones','estado']:
                        if k in payload:
                            it[k] = payload[k]
                    it['updated_at'] = str(__import__('datetime').datetime.utcnow())
                    updated = True
                    break
            if not updated:
                return jsonify({'error':'not found'}), 404
            f.seek(0); f.truncate(); json.dump(arr, f, ensure_ascii=False, indent=4)
        return jsonify({'ok':True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/entrevistas/<eid>', methods=['GET'])
def api_get_entrevista(eid):
    file_path = os.path.join('output','entrevistas.json')
    if not os.path.exists(file_path):
        return jsonify({'error':'not found'}), 404
    try:
        with open(file_path,'r',encoding='utf-8') as f:
            arr = json.load(f)
    except Exception:
        arr = []
    for it in arr:
        if it.get('id') == eid:
            return jsonify(it)
    return jsonify({'error':'not found'}), 404


@app.route('/entrevistas')
def entrevistas_view():
    return render_template('entrevistas.html')


# API para CRUD de plantillas
@app.route('/api/plantillas', methods=['GET'])
def api_get_plantillas():
    try:
        file_path = os.path.join('data', 'plantillas.json')
        if not os.path.exists(file_path):
            return jsonify([])
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plantillas', methods=['POST'])
def api_save_plantilla():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({'error': 'No data provided'}), 400
        file_path = os.path.join('data', 'plantillas.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    plantillas = json.load(f)
                except json.JSONDecodeError:
                    plantillas = []
        else:
            plantillas = []

        # If id provided, update existing
        pid = payload.get('id')
        if pid:
            updated = False
            for p in plantillas:
                if p.get('id') == pid:
                    p.update(payload)
                    p['updated_at'] = json.dumps(str(__import__('datetime').datetime.utcnow()))
                    updated = True
                    break
            if not updated:
                plantillas.append(payload)
        else:
            # create new id
            import uuid
            payload['id'] = str(uuid.uuid4())
            payload['created_at'] = json.dumps(str(__import__('datetime').datetime.utcnow()))
            plantillas.append(payload)

        # write back
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plantillas, f, ensure_ascii=False, indent=4)
        return jsonify({'ok': True, 'id': payload.get('id')}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/plantillas/<pid>', methods=['DELETE'])
def api_delete_plantilla(pid):
    try:
        # TODO: check association with vacancies (placeholder)
        file_path = os.path.join('data', 'plantillas.json')
        if not os.path.exists(file_path):
            return jsonify({'error': 'not found'}), 404
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                plantillas = json.load(f)
            except json.JSONDecodeError:
                plantillas = []
        new = [p for p in plantillas if p.get('id') != pid]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new, f, ensure_ascii=False, indent=4)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
