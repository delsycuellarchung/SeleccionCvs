import urllib.request, json, time
urls = ['http://127.0.0.1:5000/api/puestos_abiertos','http://127.0.0.1:5000/ver_cvs']
urls = ['http://127.0.0.1:5000/api/puestos_abiertos','http://127.0.0.1:5000/ver_cvs','http://127.0.0.1:5000/seleccion','http://127.0.0.1:5000/api/entrevistas','http://127.0.0.1:5000/entrevistas']
for u in urls:
    print('--- Testing', u)
    ok = False
    for i in range(10):
        try:
            with urllib.request.urlopen(u, timeout=5) as resp:
                data = resp.read().decode('utf-8')
                try:
                    obj = json.loads(data)
                    print(json.dumps(obj, ensure_ascii=False, indent=2))
                except Exception:
                    print(data)
                ok = True
                break
        except Exception as e:
            time.sleep(1)
    if not ok:
        print('FAILED:', u)
print('done')
