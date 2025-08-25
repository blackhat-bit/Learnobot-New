import os
import io
from typing import Optional, Dict, Any, List
from PIL import Image
import pytesseract
from fastapi import HTTPException, status, UploadFile
import asyncio
import tempfile

from app.config import settings


class OCRService:
    """Service for Optical Character Recognition (OCR) functionality."""
    
    def __init__(self):
        # Set Tesseract path if specified in config
        if settings.tesseract_path and os.path.exists(settings.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
    
    async def extract_text_from_image(self, image_file: UploadFile) -> Dict[str, Any]:
        """Extract text from an uploaded image file."""
        
        try:
            # Validate file type
            if not self._is_valid_image_type(image_file.content_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image format. Supported formats: JPEG, PNG, TIFF, BMP, GIF"
                )
            
            # Read image data
            image_data = await image_file.read()
            
            # Process image
            extracted_text = await self._process_image_data(image_data)
            
            return {
                "text": extracted_text["text"],
                "confidence": extracted_text["confidence"],
                "word_count": len(extracted_text["text"].split()),
                "language": extracted_text.get("language", "unknown"),
                "processing_time": extracted_text.get("processing_time", 0)
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {str(e)}"
            )
    
    async def extract_text_from_multiple_images(self, image_files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Extract text from multiple image files."""
        
        if len(image_files) > 10:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 images allowed per batch"
            )
        
        results = []
        
        for i, image_file in enumerate(image_files):
            try:
                result = await self.extract_text_from_image(image_file)
                result["file_index"] = i
                result["filename"] = image_file.filename
                results.append(result)
            except Exception as e:
                results.append({
                    "file_index": i,
                    "filename": image_file.filename,
                    "error": str(e),
                    "text": "",
                    "confidence": 0
                })
        
        return results
    
    async def _process_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """Process image data and extract text."""
        
        import time
        start_time = time.time()
        
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Preprocess image for better OCR results
            image = self._preprocess_image(image)
            
            # Extract text with confidence scores
            ocr_data = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT,
                config='--oem 3 --psm 6'  # Use LSTM OCR engine with uniform text block
            )
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])
                
                if text and conf > 0:  # Only include text with confidence > 0
                    text_parts.append(text)
                    confidences.append(conf)
            
            extracted_text = ' '.join(text_parts)
            average_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Detect language (simplified)
            detected_language = self._detect_language(extracted_text)
            
            processing_time = time.time() - start_time
            
            return {
                "text": extracted_text,
                "confidence": round(average_confidence, 2),
                "language": detected_language,
                "processing_time": round(processing_time, 2)
            }
        
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy."""
        
        # Resize image if too small or too large
        width, height = image.size
        
        # If image is very small, resize it
        if width < 300 or height < 300:
            scale_factor = max(300 / width, 300 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # If image is very large, resize it down
        elif width > 3000 or height > 3000:
            scale_factor = min(3000 / width, 3000 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character patterns."""
        
        if not text:
            return "unknown"
        
        # Simple heuristic based on character patterns
        # This is a very basic implementation
        
        # Check for common English words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if english_count > 2:
            return "en"
        
        # Check for non-ASCII characters (might indicate other languages)
        non_ascii_count = sum(1 for char in text if ord(char) > 127)
        if non_ascii_count > len(text) * 0.1:  # More than 10% non-ASCII
            return "non-english"
        
        return "en"  # Default to English
    
    def _is_valid_image_type(self, content_type: Optional[str]) -> bool:
        """Check if the uploaded file is a valid image type."""
        
        if not content_type:
            return False
        
        valid_types = [
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/tiff',
            'image/bmp',
            'image/gif'
        ]
        
        return content_type.lower() in valid_types
    
    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> Dict[str, Any]:
        """Extract text from PDF file (placeholder for future implementation)."""
        
        # This would require additional libraries like PyPDF2 or pdfplumber
        # For now, return a placeholder response
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF text extraction not yet implemented"
        )
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats."""
        
        return [
            "JPEG",
            "JPG", 
            "PNG",
            "TIFF",
            "BMP",
            "GIF"
        ]
    
    def get_ocr_health_status(self) -> Dict[str, Any]:
        """Check OCR service health and configuration."""
        
        try:
            # Test Tesseract installation
            version = pytesseract.get_tesseract_version()
            
            # Test with a simple image
            test_image = Image.new('RGB', (100, 30), color='white')
            test_result = pytesseract.image_to_string(test_image)
            
            return {
                "status": "healthy",
                "tesseract_version": str(version),
                "tesseract_path": pytesseract.pytesseract.tesseract_cmd,
                "test_successful": True
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "tesseract_path": pytesseract.pytesseract.tesseract_cmd,
                "test_successful": False
            }
