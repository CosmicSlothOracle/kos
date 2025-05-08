from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import bcrypt
import os
import json
from werkzeug.utils import secure_filename
from cms import ContentManager
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS more explicitly
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8000", "http://localhost:8080"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize CMS
content_manager = ContentManager(
    os.path.join(os.path.dirname(__file__), 'content'))

# Get the absolute path of the current directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PARTICIPANTS_FILE = os.path.join(BASE_DIR, 'participants.json')

logger.info(f'Base directory: {BASE_DIR}')
logger.info(f'Upload folder: {UPLOAD_FOLDER}')

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    logger.info(f'Creating upload directory: {UPLOAD_FOLDER}')
    os.makedirs(UPLOAD_FOLDER)
    logger.info('Upload directory created successfully')

# Create empty participants file if it doesn't exist
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

# Dummy-User (später DB)
DUMMY_USER = {
    'username': 'admin',
    # Passwort: 'kosge2024!' (bcrypt-hash)
    'password_hash': b'$2b$12$ZCgWXzUdmVX.PnIfj4oeJOkX69Tu1rVZ51zGYe3kSloANnwMaTlBW'
}

ALLOWED_EXTENSIONS = {'png'}


def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get(
        'Origin')
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS, PUT'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


@app.after_request
def after_request(response):
    return add_cors_headers(response)


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin",
                             request.headers.get('Origin'))
        response.headers.add("Access-Control-Allow-Methods",
                             "GET, POST, DELETE, OPTIONS, PUT")
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type, Authorization")
        return response


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_participants():
    if not os.path.exists(PARTICIPANTS_FILE):
        return []
    with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_participants(participants):
    with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username == DUMMY_USER['username'] and bcrypt.checkpw(password.encode(), DUMMY_USER['password_hash']):
        # Dummy-Token (später JWT)
        return jsonify({'token': 'dummy-token', 'user': username}), 200
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/banners', methods=['POST'])
def upload_banner():
    if 'file' not in request.files:
        logger.error('No file part in request')
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f'Saving file to: {save_path}')
        try:
            file.save(save_path)
            logger.info(f'File saved successfully: {save_path}')
            # Verify file exists after saving
            if os.path.exists(save_path):
                logger.info(f'File exists at: {save_path}')
                logger.info(f'File size: {os.path.getsize(save_path)} bytes')
            else:
                logger.error(f'File not found after saving: {save_path}')
            url = f'/api/uploads/{filename}'
            return jsonify({'url': url, 'filename': filename}), 201
        except Exception as e:
            logger.error(f'Error saving file: {str(e)}')
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    logger.error('Invalid file type')
    return jsonify({'error': 'Invalid file type. Only PNG allowed.'}), 400


@app.route('/api/banners', methods=['GET'])
def list_banners():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    urls = [f'/api/uploads/{f}' for f in files]
    return jsonify({'banners': urls}), 200


@app.route('/api/banners/<filename>', methods=['DELETE'])
def delete_banner(filename):
    filename = secure_filename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not allowed_file(filename):
        return jsonify({'error': 'Invalid file type.'}), 400
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True, 'filename': filename}), 200
    else:
        return jsonify({'error': 'File not found.'}), 404


@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    logger.info(f'Attempting to serve file: {filename}')
    logger.info(f'Upload folder: {UPLOAD_FOLDER}')
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    logger.info(f'Full file path: {file_path}')

    if not os.path.exists(file_path):
        logger.error(f'File not found: {file_path}')
        return jsonify({'error': 'File not found'}), 404

    try:
        logger.info(f'File exists, size: {os.path.getsize(file_path)} bytes')
        response = send_from_directory(UPLOAD_FOLDER, filename)

        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'

        # Set content type for PNG files
        if filename.lower().endswith('.png'):
            response.headers['Content-Type'] = 'image/png'

        return response
    except Exception as e:
        logger.error(f'Error serving file {filename}: {str(e)}')
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500


@app.route('/api/participants', methods=['POST'])
def add_participant():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    banner = data.get('banner')
    if not name:
        return jsonify({'error': 'Name ist erforderlich.'}), 400
    participant = {
        'name': name,
        'email': email,
        'message': message,
        'banner': banner
    }
    participants = load_participants()
    participants.append(participant)
    save_participants(participants)
    return jsonify({'success': True, 'participant': participant}), 201


@app.route('/api/participants', methods=['GET'])
def get_participants():
    participants = load_participants()
    return jsonify({'participants': participants}), 200


# CMS Routes
@app.route('/api/cms/content/<section>', methods=['GET'])
def get_content(section):
    language = request.args.get('language')
    content = content_manager.get_content(section, language)
    if content:
        return jsonify(content), 200
    return jsonify({'error': 'Content not found'}), 404


@app.route('/api/cms/content/<section>', methods=['POST'])
def create_content(section):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    metadata = data.get('metadata', {})

    if not all([title, content]):
        return jsonify({'error': 'Title and content are required'}), 400

    success = content_manager.create_content(section, title, content, metadata)
    if success:
        return jsonify({'success': True, 'section': section}), 201
    return jsonify({'error': 'Failed to create content'}), 500


@app.route('/api/cms/content/<section>', methods=['PUT'])
def update_content(section):
    data = request.get_json()
    content = data.get('content')
    metadata = data.get('metadata', {})
    language = data.get('language')

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    success = content_manager.update_content(
        section, content, metadata, language)
    if success:
        return jsonify({'success': True, 'section': section}), 200
    return jsonify({'error': 'Failed to update content'}), 404


@app.route('/api/cms/content/<section>/translate/<target_language>', methods=['POST'])
def translate_content(section, target_language):
    success = content_manager.translate_content(section, target_language)
    if success:
        return jsonify({'success': True, 'section': section, 'language': target_language}), 200
    return jsonify({'error': 'Translation failed'}), 400


@app.route('/api/cms/sections', methods=['GET'])
def list_sections():
    language = request.args.get('language')
    sections = content_manager.list_sections(language)
    return jsonify({'sections': sections}), 200


@app.route('/api/cms/content/<section>', methods=['DELETE'])
def delete_content(section):
    language = request.args.get('language')
    success = content_manager.delete_content(section, language)
    if success:
        return jsonify({'success': True}), 200
    return jsonify({'error': 'Content not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
