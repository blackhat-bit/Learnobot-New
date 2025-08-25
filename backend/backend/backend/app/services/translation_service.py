from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
import asyncio
import httpx
from googletrans import Translator
import json

from app.config import settings


class TranslationService:
    """Service for text translation functionality."""
    
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = self._get_supported_languages()
    
    async def translate_text(
        self, 
        text: str, 
        target_language: str, 
        source_language: str = "auto"
    ) -> Dict[str, Any]:
        """Translate text from source language to target language."""
        
        try:
            if not text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text cannot be empty"
                )
            
            # Validate target language
            if target_language not in self.supported_languages:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported target language: {target_language}"
                )
            
            # Perform translation
            result = await self._translate_with_googletrans(text, target_language, source_language)
            
            return {
                "original_text": text,
                "translated_text": result["translated_text"],
                "source_language": result["detected_language"],
                "target_language": target_language,
                "confidence": result.get("confidence", 1.0),
                "service": "google_translate"
            }
        
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation failed: {str(e)}"
            )
    
    async def translate_multiple_texts(
        self,
        texts: List[str],
        target_language: str,
        source_language: str = "auto"
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts."""
        
        if len(texts) > 100:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 texts allowed per batch"
            )
        
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = await self.translate_text(text, target_language, source_language)
                result["text_index"] = i
                results.append(result)
            except Exception as e:
                results.append({
                    "text_index": i,
                    "original_text": text,
                    "translated_text": "",
                    "error": str(e),
                    "source_language": "unknown",
                    "target_language": target_language,
                    "confidence": 0.0
                })
        
        return results
    
    async def _translate_with_googletrans(
        self, 
        text: str, 
        target_language: str, 
        source_language: str
    ) -> Dict[str, Any]:
        """Translate using googletrans library."""
        
        try:
            # Run translation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            translation = await loop.run_in_executor(
                None, 
                lambda: self.translator.translate(
                    text, 
                    dest=target_language, 
                    src=source_language if source_language != "auto" else None
                )
            )
            
            return {
                "translated_text": translation.text,
                "detected_language": translation.src,
                "confidence": getattr(translation, 'confidence', 1.0)
            }
        
        except Exception as e:
            raise Exception(f"Google Translate error: {str(e)}")
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of the given text."""
        
        try:
            if not text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text cannot be empty"
                )
            
            loop = asyncio.get_event_loop()
            detection = await loop.run_in_executor(
                None,
                lambda: self.translator.detect(text)
            )
            
            language_name = self.supported_languages.get(detection.lang, "Unknown")
            
            return {
                "text": text,
                "detected_language": detection.lang,
                "language_name": language_name,
                "confidence": detection.confidence
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Language detection failed: {str(e)}"
            )
    
    def _get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages mapping."""
        
        # Common language codes and names
        return {
            'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic',
            'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
            'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
            'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)', 'co': 'Corsican', 'hr': 'Croatian',
            'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English',
            'eo': 'Esperanto', 'et': 'Estonian', 'tl': 'Filipino', 'fi': 'Finnish',
            'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian',
            'de': 'German', 'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole',
            'ha': 'Hausa', 'haw': 'Hawaiian', 'iw': 'Hebrew', 'he': 'Hebrew',
            'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian', 'is': 'Icelandic',
            'ig': 'Igbo', 'id': 'Indonesian', 'ga': 'Irish', 'it': 'Italian',
            'ja': 'Japanese', 'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh',
            'km': 'Khmer', 'ko': 'Korean', 'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz',
            'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian',
            'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
            'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori',
            'mr': 'Marathi', 'mn': 'Mongolian', 'my': 'Myanmar (Burmese)',
            'ne': 'Nepali', 'no': 'Norwegian', 'or': 'Odia', 'ps': 'Pashto',
            'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi',
            'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan', 'gd': 'Scots Gaelic',
            'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona', 'sd': 'Sindhi',
            'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali',
            'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish',
            'tg': 'Tajik', 'ta': 'Tamil', 'te': 'Telugu', 'th': 'Thai',
            'tr': 'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'ug': 'Uyghur',
            'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa',
            'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported languages."""
        return self.supported_languages
    
    def get_popular_languages(self) -> List[Dict[str, str]]:
        """Get list of popular languages for UI display."""
        
        popular_codes = [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
            'ar', 'hi', 'bn', 'pa', 'te', 'mr', 'ta', 'ur', 'gu', 'kn',
            'ml', 'th', 'vi', 'id', 'ms', 'tl', 'tr', 'pl', 'nl', 'sv'
        ]
        
        return [
            {"code": code, "name": self.supported_languages[code]}
            for code in popular_codes
            if code in self.supported_languages
        ]
    
    async def translate_conversation(
        self, 
        messages: List[Dict[str, str]], 
        target_language: str
    ) -> List[Dict[str, Any]]:
        """Translate an entire conversation while preserving structure."""
        
        translated_messages = []
        
        for message in messages:
            if "content" in message:
                try:
                    translation_result = await self.translate_text(
                        message["content"], 
                        target_language
                    )
                    
                    translated_message = message.copy()
                    translated_message["original_content"] = message["content"]
                    translated_message["content"] = translation_result["translated_text"]
                    translated_message["translation_info"] = {
                        "source_language": translation_result["source_language"],
                        "target_language": target_language,
                        "confidence": translation_result["confidence"]
                    }
                    
                    translated_messages.append(translated_message)
                
                except Exception as e:
                    # Keep original message if translation fails
                    error_message = message.copy()
                    error_message["translation_error"] = str(e)
                    translated_messages.append(error_message)
            else:
                translated_messages.append(message)
        
        return translated_messages
    
    def get_service_health(self) -> Dict[str, Any]:
        """Check translation service health."""
        
        try:
            # Test with a simple translation
            test_translation = self.translator.translate("Hello", dest='es')
            
            return {
                "status": "healthy",
                "service": "google_translate",
                "test_successful": True,
                "supported_languages_count": len(self.supported_languages)
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "google_translate",
                "error": str(e),
                "test_successful": False
            }
