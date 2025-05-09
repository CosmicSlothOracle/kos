import os
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, UPLOAD_FOLDER


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file(file):
    """Validate uploaded file"""
    if file.filename == '':
        return False, "No selected file"

    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"

    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > MAX_CONTENT_LENGTH:
            return False, f"File too large. Maximum size: {MAX_CONTENT_LENGTH / (1024 * 1024)}MB"
    except Exception as e:
        return False, f"Error checking file size: {str(e)}"

    return True, None


def save_file(file):
    """Save uploaded file"""
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # If file exists, append number to filename
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{ext}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            counter += 1

        file.save(file_path)

        # Verify file was saved
        if not os.path.exists(file_path):
            return False, "Failed to save file"

        return True, filename
    except Exception as e:
        return False, f"Error saving file: {str(e)}"


def delete_file(filename):
    """Delete file from uploads directory"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, None
        return False, "File not found"
    except Exception as e:
        return False, f"Error deleting file: {str(e)}"


def get_file_info(filename):
    """Get file information"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(file_path):
            return {
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path),
                'type': os.path.splitext(filename)[1][1:].lower()
            }
        return None
    except Exception:
        return None
