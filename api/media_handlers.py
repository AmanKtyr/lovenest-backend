from PIL import Image
import io
import os
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

def compress_image(image_file, max_size=(1920, 1920), quality=85):
    """
    Compresses an image to a maximum dimension and reduces quality.
    Strictly enforces a 2MB (2,097,152 bytes) limit.
    """
    img = Image.open(image_file)
    
    # Convert RGBA to RGB if necessary (for JPEG support)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Industrial Ready: Higher cap for better clarity on large screens
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Iterative compression to stay under 2MB
    MAX_BYTES = 2 * 1024 * 1024
    current_quality = quality
    
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=current_quality, optimize=True)
        size = buffer.tell()
        
        if size <= MAX_BYTES or current_quality <= 20:
            buffer.seek(0)
            return ContentFile(buffer.getvalue(), name=os.path.basename(image_file.name))
        
        # Reduce quality and try again
        current_quality -= 10

def get_cipher():
    """Returns a Fernet cipher using the key from settings."""
    key = getattr(settings, 'IMAGE_ENCRYPTION_KEY', None)
    if not key:
        # Fallback or error? For professional use, we should raise an error if key is missing.
        raise ValueError("IMAGE_ENCRYPTION_KEY is not set in settings.")
    return Fernet(key.encode())

def encrypt_image(image_content):
    """Encrypts image bytes."""
    cipher = get_cipher()
    return cipher.encrypt(image_content)

def decrypt_image(encrypted_content):
    """Decrypts image bytes."""
    cipher = get_cipher()
    try:
        return cipher.decrypt(encrypted_content)
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise
