# app/services/vision_service.py
import logging
from typing import Dict, Any
from app.ai.multi_llm_manager import multi_llm_manager

logger = logging.getLogger(__name__)


class VisionService:
    """Service for processing images with vision-capable AI models"""
    
    @staticmethod
    def supports_vision(provider: str) -> bool:
        """Check if a provider supports vision API"""
        if not provider or provider not in multi_llm_manager.providers:
            return False
        
        provider_instance = multi_llm_manager.providers[provider]
        
        # Check if provider has process_image method
        return hasattr(provider_instance, 'process_image')
    
    @staticmethod
    async def process_image_with_vision(
        image_data: bytes,
        prompt: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Process image using vision API
        
        Args:
            image_data: Raw image bytes
            prompt: Text prompt/question about the image
            provider: Provider key (e.g., "google-gemini_2_5_flash", "openai", "anthropic")
        
        Returns:
            Dictionary with:
                - response: AI's response about the image
                - provider: Provider used
                - success: Whether processing succeeded
        """
        import time
        
        start_time = time.time()
        
        try:
            if not VisionService.supports_vision(provider):
                raise ValueError(f"Provider {provider} does not support vision API")
            
            provider_instance = multi_llm_manager.providers[provider]
            
            logger.info(f"Processing image with vision provider: {provider}")
            
            # Call vision API
            response_text = provider_instance.process_image(
                image_data=image_data,
                prompt=prompt
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Vision processing completed in {processing_time:.2f}s")
            
            return {
                "response": response_text,
                "provider": provider,
                "success": True,
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Vision processing failed after {processing_time:.2f}s: {str(e)}")
            
            return {
                "response": None,
                "provider": provider,
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    @staticmethod
    async def process_multiple_images_with_vision(
        images_data: list,
        prompt: str,
        provider: str
    ) -> Dict[str, Any]:
        """
        Process multiple images together using vision API
        
        Args:
            images_data: List of raw image bytes
            prompt: Text prompt/question about the images
            provider: Provider key (e.g., "google-gemini_2_5_flash", "openai", "anthropic")
        
        Returns:
            Dictionary with:
                - response: AI's response about the images
                - provider: Provider used
                - success: Whether processing succeeded
        """
        import time
        
        start_time = time.time()
        
        try:
            if not VisionService.supports_vision(provider):
                raise ValueError(f"Provider {provider} does not support vision API")
            
            provider_instance = multi_llm_manager.providers[provider]
            
            logger.info(f"Processing {len(images_data)} images together with vision provider: {provider}")
            
            # Check if provider supports multiple images
            if hasattr(provider_instance, 'process_multiple_images'):
                # Use dedicated multi-image method
                response_text = provider_instance.process_multiple_images(
                    images_data=images_data,
                    prompt=prompt
                )
            else:
                # Fallback: process first image only
                logger.warning(f"Provider {provider} doesn't support multiple images, using first image only")
                response_text = provider_instance.process_image(
                    image_data=images_data[0],
                    prompt=prompt
                )
            
            processing_time = time.time() - start_time
            logger.info(f"Multi-image vision processing completed in {processing_time:.2f}s")
            
            return {
                "response": response_text,
                "provider": provider,
                "success": True,
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Multi-image vision processing failed after {processing_time:.2f}s: {str(e)}")
            
            return {
                "response": None,
                "provider": provider,
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    @staticmethod
    def get_vision_capable_providers() -> list:
        """Get list of all providers that support vision"""
        vision_providers = []
        
        for provider_key, provider_instance in multi_llm_manager.providers.items():
            if hasattr(provider_instance, 'process_image'):
                info = provider_instance.get_info()
                vision_providers.append({
                    "key": provider_key,
                    "name": info.get("provider", "Unknown"),
                    "model": info.get("model", "unknown")
                })
        
        return vision_providers


# Singleton instance
vision_service = VisionService()

