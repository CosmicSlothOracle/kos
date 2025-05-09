import os

# Base Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PARTICIPANTS_FILE = os.path.join(BASE_DIR, 'participants.json')

# File Upload Settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8080",
    "https://kos-frontend.onrender.com",
    "https://kos-frontend-kqxo.onrender.com",
    "https://kosge-berlin.de",
    "http://kosge-berlin.de"
]

# Authentication Settings
ADMIN_USER = {
    'username': 'admin',
    # Password: 'kosge2024!' (bcrypt-hash)
    'password_hash': b'$2b$12$ZCgWXzUdmVX.PnIfj4oeJOkX69Tu1rVZ51zGYe3kSloANnwMaTlBW'
}

# Content Management Settings
SUPPORTED_LANGUAGES = ['de', 'en', 'tr', 'ru', 'ar']
DEFAULT_LANGUAGE = 'de'

# Create required directories


def init_directories():
    """Initialize required directories"""
    directories = [
        UPLOAD_FOLDER,
        os.path.join(BASE_DIR, 'content')
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Create language directories
    content_dir = os.path.join(BASE_DIR, 'content')
    for lang in SUPPORTED_LANGUAGES:
        lang_dir = os.path.join(content_dir, lang)
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)

# Create empty participants file if it doesn't exist


def init_participants_file():
    """Initialize participants file if it doesn't exist"""
    if not os.path.exists(PARTICIPANTS_FILE):
        with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
            f.write('[]')


def init():
    """Initialize all required configurations"""
    init_directories()
    init_participants_file()
