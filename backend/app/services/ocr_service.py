# app/services/ocr_service.py
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

async def extract_text(image_data: bytes) -> str:
    """Extract text from image using OCR"""
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Extract text using Tesseract
        # Configure for Hebrew + English
        text = pytesseract.image_to_string(
            image,
            lang='heb+eng',
            config='--psm 6'  # Assume uniform block of text
        )
        
        # Clean up the text
        text = text.strip()
        
        logger.info(f"Extracted text: {text[:100]}...")
        return text
        
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        raise Exception("Failed to extract text from image")