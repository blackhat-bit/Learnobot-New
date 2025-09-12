# app/services/ocr_service.py
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

async def extract_text(image_data: bytes) -> str:
    """Extract text from image using OCR with Hebrew optimization"""
    try:
        # Validate image data
        if not image_data or len(image_data) == 0:
            logger.error("Empty image data provided")
            return "שגיאה: התמונה ריקה או פגומה."
        
        # Convert bytes to PIL Image
        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            return "שגיאה: לא ניתן לפתוח את התמונה. אנא נסה תמונה אחרת."
        
        # Check image format
        if image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
            logger.warning(f"Unsupported image format: {image.format}")
        
        # Optimize image for OCR (resize if too small, enhance contrast)
        width, height = image.size
        logger.info(f"Original image size: {width}x{height}")
        
        if width < 600 or height < 600:
            # Scale up small images
            scale_factor = max(600/width, 600/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            logger.info(f"Scaled image to: {new_width}x{new_height}")
        
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
        
        for i, config in enumerate(configs):
            try:
                logger.info(f"Trying OCR config {i+1}: {config}")
                text = pytesseract.image_to_string(
                    image,
                    lang='heb+eng',
                    config=config
                )
                
                text = text.strip()
                if len(text) > len(best_text):
                    best_text = text
                    logger.info(f"Config {i+1} produced text: {text[:50]}...")
                    
            except Exception as e:
                logger.warning(f"OCR config {i+1} failed: {str(e)}")
                continue
        
        # Clean up the text
        if best_text and len(best_text.strip()) > 2:
            # Remove extra whitespace
            best_text = ' '.join(best_text.split())
            logger.info(f"Final extracted text: {best_text[:100]}...")
            return best_text
        else:
            logger.warning("No text extracted from image")
            return "לא הצלחתי לקרוא את התמונה. נסה תמונה בהירה וברורה יותר."
        
    except Exception as e:
        logger.error(f"OCR failed with error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return "שגיאה בקריאת התמונה. אנא נסה שוב או כתב את השאלה ידנית."