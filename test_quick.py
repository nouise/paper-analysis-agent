import requests
import time

DB_ID = 'kb_b6fbe3d3f9933339e1a3016dafcf54a3'
BASE_URL = 'http://localhost:8003'

# Create unique test file
test_content = f"Test document {time.time()}\nMachine learning and AI research."
with open('test_unique.txt', 'w') as f:
    f.write(test_content)

# Upload
with open('test_unique.txt', 'rb') as f:
    files = {'file': ('test_unique.txt', f, 'text/plain')}
    params = {'db_id': DB_ID}
    r = requests.post(f'{BASE_URL}/knowledge/files/upload', files=files, params=params)
    print(f'Upload: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'File path: {data["file_path"]}')
        print(f'Parsed: {data["parsed"]}, Length: {data["content_length"]}')

        # Add to KB
        add_data = {'items': [data['file_path']], 'params': {'content_type': 'file'}}
        r2 = requests.post(f'{BASE_URL}/knowledge/databases/{DB_ID}/documents', json=add_data)
        print(f'\nAdd to KB: {r2.status_code}')
        if r2.status_code == 200:
            result = r2.json()
            print(f'Status: {result}')

        # Check DB info
        r3 = requests.get(f'{BASE_URL}/knowledge/databases/{DB_ID}')
        db = r3.json()
        print(f'\nFiles in DB: {len(db.get("files", {}))}')
        for fid, f in db.get('files', {}).items():
            print(f'  - {f.get("filename")} ({f.get("type")}, {f.get("status")})')
    else:
        print(f'Error: {r.text}')
