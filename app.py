from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import bcrypt
import os
import json
from werkzeug.utils import secure_filename
from cms import ContentManager
import logging
from config import (
    UPLOAD_FOLDER, PARTICIPANTS_FILE, ADMIN_USER,
    CORS_ORIGINS, MAX_CONTENT_LENGTH, init
)
from utils import validate_file, save_file, delete_file, get_file_info
import datetime

# Initialize configuration
init()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "DELETE", "OPTIONS", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize CMS
content_manager = ContentManager(
    os.path.join(os.path.dirname(__file__), 'content'))


def add_cors_headers(response):
    """Add CORS headers to response"""
    if request.headers.get('Origin') in CORS_ORIGINS:
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
        if request.headers.get('Origin') in CORS_ORIGINS:
            response.headers.add("Access-Control-Allow-Origin",
                                 request.headers.get('Origin'))
            response.headers.add("Access-Control-Allow-Methods",
                                 "GET, POST, DELETE, OPTIONS, PUT")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type, Authorization")
        return response


def load_participants():
    """Load participants from JSON file"""
    if not os.path.exists(PARTICIPANTS_FILE):
        return []
    with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception as e:
            logger.error(f"Error loading participants: {str(e)}")
            return []


def save_participants(participants):
    """Save participants to JSON file"""
    try:
        with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(participants, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving participants: {str(e)}")
        return False


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        if username == ADMIN_USER['username'] and bcrypt.checkpw(password.encode(), ADMIN_USER['password_hash']):
            return jsonify({'token': 'dummy-token', 'user': username}), 200

        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/banners', methods=['POST'])
def upload_banner():
    """Upload banner endpoint"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    valid, error = validate_file(file)

    if not valid:
        return jsonify({'error': error}), 400

    success, result = save_file(file)

    if not success:
        return jsonify({'error': result}), 500

    url = f'/api/uploads/{result}'
    return jsonify({'url': url, 'filename': result}), 201


@app.route('/api/banners', methods=['GET'])
def list_banners():
    """List banners endpoint"""
    try:
        files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(
            os.path.join(UPLOAD_FOLDER, f))]
        urls = []

        for f in files:
            info = get_file_info(f)
            if info:
                urls.append({
                    'url': f'/api/uploads/{f}',
                    'filename': f,
                    'size': info['size'],
                    'modified': info['modified'],
                    'type': info['type']
                })

        return jsonify({'banners': urls}), 200
    except Exception as e:
        logger.error(f"Error listing banners: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/banners/<filename>', methods=['DELETE'])
def delete_banner(filename):
    """Delete banner endpoint"""
    success, error = delete_file(filename)

    if success:
        return jsonify({'success': True, 'filename': filename}), 200
    return jsonify({'error': error}), 404


@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded file endpoint"""
    try:
        info = get_file_info(filename)
        if not info:
            return jsonify({'error': 'File not found'}), 404

        response = send_from_directory(UPLOAD_FOLDER, filename)
        response.headers['Content-Type'] = f'image/{info["type"]}'
        return response
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500


@app.route('/api/participants', methods=['POST'])
def add_participant():
    try:
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
            'banner': banner,
            'timestamp': datetime.datetime.now().isoformat()
        }

        participants = load_participants()
        participants.append(participant)

        if not save_participants(participants):
            return jsonify({'error': 'Fehler beim Speichern der Teilnahme.'}), 500

        return jsonify({'success': True, 'participant': participant}), 201
    except Exception as e:
        logger.error(f"Error adding participant: {str(e)}")
        return jsonify({'error': 'Interner Serverfehler'}), 500


@app.route('/api/participants', methods=['GET'])
def get_participants():
    try:
        participants = load_participants()
        # Sort participants by timestamp if it exists, newest first
        participants.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify({'participants': participants}), 200
    except Exception as e:
        logger.error(f"Error getting participants: {str(e)}")
        return jsonify({'error': 'Fehler beim Laden der Teilnahmen'}), 500

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
