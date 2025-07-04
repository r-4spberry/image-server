from flask import Flask
from flask import request, jsonify
from secrets import choice
from PIL import Image
import string
from flask import send_from_directory
from werkzeug.utils import secure_filename

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
    app.run(debug=True)