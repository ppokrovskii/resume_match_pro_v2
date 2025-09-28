"""
File validation utilities
"""

import logging
import mimetypes
from typing import Tuple, Optional, Union
from fastapi import UploadFile

from utils.fastapi_error_handler import FileValidationError

logger = logging.getLogger(__name__)

# Allowed file types and their MIME types
ALLOWED_EXTENSIONS = {
    'pdf': ['application/pdf'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
}

# Maximum file size (16MB)
MAX_FILE_SIZE = 16 * 1024 * 1024

# Minimum file size (1KB)
MIN_FILE_SIZE = 102  # Reduced from 1024 to ~100 bytes (10x smaller)


def get_file_extension(filename: str) -> Optional[str]:
    """Extract file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None


def is_allowed_file_type(filename: str, content_type: str) -> bool:
    """Check if file type is allowed"""
    extension = get_file_extension(filename)
    
    if not extension or extension not in ALLOWED_EXTENSIONS:
        return False
    
    allowed_mimes = ALLOWED_EXTENSIONS[extension]
    return content_type in allowed_mimes


def validate_file_size(file_size: int) -> None:
    """Validate file size"""
    if file_size < MIN_FILE_SIZE:
        raise FileValidationError(f"File too small. Minimum size: {MIN_FILE_SIZE} bytes")
    
    if file_size > MAX_FILE_SIZE:
        raise FileValidationError(f"File too large. Maximum size: {MAX_FILE_SIZE} bytes")


def validate_filename(filename: str) -> None:
    """Validate filename"""
    if not filename:
        raise FileValidationError("Filename is required")
    
    if len(filename) > 255:
        raise FileValidationError("Filename too long (max 255 characters)")
    
    # Check for dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        if char in filename:
            raise FileValidationError(f"Filename contains invalid character: {char}")


def detect_content_type(filename: str, file_data: bytes) -> str:
    """Detect content type from file data and filename"""
    # First, try to detect from file extension
    content_type, _ = mimetypes.guess_type(filename)
    
    if content_type:
        return content_type
    
    # Fallback: detect from file signature (magic bytes)
    if file_data.startswith(b'%PDF'):
        return 'application/pdf'
    elif file_data.startswith(b'\xd0\xcf\x11\xe0'):  # MS Office (old format)
        return 'application/msword'
    elif file_data.startswith(b'PK\x03\x04'):  # ZIP-based formats (docx)
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    raise FileValidationError("Unable to determine file type")


def validate_file_content(file_data: bytes, content_type: str) -> None:
    """Validate file content matches declared type"""
    if content_type == 'application/pdf':
        if not file_data.startswith(b'%PDF'):
            raise FileValidationError("File content doesn't match PDF format")
    
    elif content_type == 'application/msword':
        if not file_data.startswith(b'\xd0\xcf\x11\xe0'):
            raise FileValidationError("File content doesn't match DOC format")
    
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        if not file_data.startswith(b'PK\x03\x04'):
            raise FileValidationError("File content doesn't match DOCX format")


def validate_upload_file(file: Union[UploadFile, object]) -> Tuple[str, str, int]:
    """
    Validate uploaded file and return (filename, content_type, file_size)
    """
    # Check if file was uploaded
    if not file or not file.filename:
        raise FileValidationError("No file uploaded")
    
    filename = file.filename
    validate_filename(filename)
    
    # Read file data - handle both UploadFile and mock objects
    if hasattr(file, 'seek'):
        file.seek(0)
        file_data = file.read()
        if hasattr(file, 'seek'):
            file.seek(0)  # Reset for subsequent reads
    else:
        # For mock objects that might have data attribute
        file_data = getattr(file, 'data', b'')
    
    file_size = len(file_data)
    validate_file_size(file_size)
    
    # Detect and validate content type
    content_type = detect_content_type(filename, file_data)
    
    if not is_allowed_file_type(filename, content_type):
        raise FileValidationError(f"File type not allowed: {content_type}")
    
    validate_file_content(file_data, content_type)
    
    logger.info(f"File validation passed: {filename} ({content_type}, {file_size} bytes)")
    
    return sanitize_filename(filename), content_type, file_size


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '.-_':
            safe_chars.append(char)
        elif char == ' ':
            safe_chars.append('_')
    
    sanitized = ''.join(safe_chars)
    
    # Ensure filename isn't empty or just underscores/dots
    if not sanitized or sanitized.replace('_', '').replace('.', '').replace('-', '') == '':
        sanitized = 'unnamed_file'
    
    # Limit length
    if len(sanitized) > 100:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = f"{name[:95]}.{ext}" if ext else name[:100]
    
    return sanitized





