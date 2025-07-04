from pathlib import Path
from flask import Flask
from flask import request, jsonify
from secrets import choice
from PIL import Image
import string
from flask import send_from_directory
from werkzeug.utils import secure_filename


MAX_FOLDER_SIZE = 1 * 1024**3      # 1 GB
TARGET_FOLDER_SIZE = 800 * 1024**2 # 800 MB

def cleanup_folder(path='images'):
    folder = Path(path)
    files = sorted(folder.glob('*'), key=lambda f: f.stat().st_mtime)  # oldest first
    total_size = sum(f.stat().st_size for f in files)

    while total_size > MAX_FOLDER_SIZE and files:
        file_to_remove = files.pop(0)
        try:
            total_size -= file_to_remove.stat().st_size
            file_to_remove.unlink()
            print(f"Deleted: {file_to_remove.name}")
        except Exception as e:
            print(f"Failed to delete {file_to_remove.name}: {e}")

alphabet = string.ascii_lowercase + string.digits
def get_name(len = 8):
    return ''.join(choice(alphabet) for _ in range(len))

app = Flask(__name__)


@app.post('/upload')
def upload():
    try:
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file part in the request'}), 400
        
        file = request.files['image'] 
        
        Image.open(file.stream).verify()
        
        filename = secure_filename(get_name() + '.png')
        file.stream.seek(0)
        cleanup_folder()
        file.save('images/' + filename)
        return jsonify({'status': 'success', 'message': 'File uploaded successfully', 'path': 'images/' + filename}), 200
    except Image.UnidentifiedImageError:
        return jsonify({'status': 'error', 'message': 'Invalid image file'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.get('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.get('/images/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory('images', filename)
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
if __name__ == '__main__':
    app.run('0.0.0.0', 5000)