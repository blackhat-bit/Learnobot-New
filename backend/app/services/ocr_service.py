# app/services/ocr_service.py
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

async def extract_text(image_data: bytes) -> str:
    """Extract text from image using OCR with Hebrew optimization"""
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Optimize image for OCR (resize if too small, enhance contrast)
        width, height = image.size
        if width < 600 or height < 600:
            # Scale up small images
            scale_factor = max(600/width, 600/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to grayscale for better OCR
        if image.mode != 'L':
            image = image.convert('L')
        
        # Try multiple OCR configurations for Hebrew text
        configs = [
            '--psm 6 -c tessedit_char_whitelist=אבגדהוזחטיכלמנסעפצקרשת0123456789.,!?:״׳()[]{}+-=*/% abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 7',  # Single text line
            '--psm 8',  # Single word
            '--psm 6'   # Uniform block of text (default)
        ]
        
        best_text = ""
        best_confidence = 0
        
        for config in configs:
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang='heb+eng',
                    config=config
                )
                
                text = text.strip()
                if len(text) > len(best_text):
                    best_text = text
                    
            except:
                continue
        
        # Clean up the text
        if best_text:
            # Remove extra whitespace
            best_text = ' '.join(best_text.split())
            logger.info(f"Extracted text: {best_text[:100]}...")
            return best_text
        else:
            return "לא הצלחתי לקרוא את התמונה. נסה תמונה בהירה וברורה יותר."
        
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        return "שגיאה בקריאת התמונה. אנא נסה שוב או כתב את השאלה ידנית."