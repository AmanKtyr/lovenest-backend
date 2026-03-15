from PIL import Image
import io
import os
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

def compress_image(image_file, max_size=(1080, 1080), quality=75):
    """
    Compresses an image to a maximum dimension and reduces quality.
    Returns a ContentFile ready for Django's ImageField.
    """
    img = Image.open(image_file)
    
    # Convert RGBA to RGB if necessary (for PNGs)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Resize if larger than max_size while maintaining aspect ratio
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    
    # Get values and return ContentFile
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=os.path.basename(image_file.name))

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
