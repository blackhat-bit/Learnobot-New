# app/api/llm_management.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.llm_config import LLMConfig
from app.ai.multi_llm_manager import multi_llm_manager
from app.schemas.llm_config import (
    LLMProviderInfo, LLMConfigCreate, LLMConfigUpdate,
    ProviderComparison, SystemPromptUpdate, APIKeyUpdate, 
    APIKeyResponse, ProviderStatus, ModelDeactivationUpdate
)
from app.ai.prompts import HEBREW_PRACTICE_PROMPT, HEBREW_TEST_PROMPT

# Default prompts for different modes
DEFAULT_PROMPTS = {
    "practice": HEBREW_PRACTICE_PROMPT.template,
    "test": HEBREW_TEST_PROMPT.template,
}

router = APIRouter()

@router.get("/providers", response_model=List[LLMProviderInfo])
async def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """Get list of all available LLM providers"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return multi_llm_manager.get_available_providers()

@router.get("/models")
async def get_available_models(
    current_user: User = Depends(get_current_user)
):
    """Get list of available models grouped by provider type"""
    # Allow students to see available models for selection
    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Students only see active (non-deactivated) models
    if current_user.role == UserRole.STUDENT:
        return multi_llm_manager.get_active_models()
    else:
        # Teachers and admins see all models (including deactivated ones)
        return multi_llm_manager.get_available_models()

@router.post("/providers/{provider_name}/activate")
async def set_active_provider(
    provider_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Switch to a different LLM provider"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can change providers")
    
    try:
        multi_llm_manager.set_active_provider(provider_name)
        return {"message": f"Switched to {provider_name}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/compare", response_model=Dict[str, Any])
async def compare_providers(
    comparison_request: ProviderComparison,
    current_user: User = Depends(get_current_user)
):
    """Compare responses from multiple providers"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can compare providers")
    
    results = multi_llm_manager.compare_providers(
        prompt=comparison_request.prompt,
        providers=comparison_request.providers
    )
    
    return results

@router.post("/test-mode/{mode}")
async def test_with_mode(
    mode: str,
    test_prompt: str,
    provider: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test a specific mode (practice/test) with different providers"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Apply mode-specific prompting
    if mode == "practice":
        full_prompt = f"You are helping a student learn. Be encouraging and detailed.\n\n{test_prompt}"
    else:  # test mode
        full_prompt = f"You are in test mode. Provide minimal assistance only.\n\n{test_prompt}"
    
    response = multi_llm_manager.generate(full_prompt, provider=provider)
    
    return {
        "mode": mode,
        "provider": provider or multi_llm_manager.active_provider,
        "response": response
    }

    # Add to app/api/llm_management.py (additional endpoints)

@router.post("/prompts/{mode}")
async def update_prompt_config(
    mode: str,
    config: SystemPromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update prompt configuration for a specific mode"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if mode not in ["practice", "test"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    # Save to database - ONE global config per mode (not per manager)
    config_entry = db.query(LLMConfig).filter(
        LLMConfig.name == f"{mode}_mode"
    ).first()
    
    if config_entry:
        # Update existing global config
        config_entry.system_prompt = config.system
        config_entry.temperature = config.temperature
        config_entry.max_tokens = config.maxTokens
        config_entry.updated_at = datetime.utcnow()
        config_entry.created_by = current_user.id  # Track who last updated
    else:
        # Create new global config
        config_entry = LLMConfig(
            provider_id=1,  # Default provider
            name=f"{mode}_mode",
            model=multi_llm_manager.active_provider,
            temperature=config.temperature,
            max_tokens=config.maxTokens,
            system_prompt=config.system,
            created_by=current_user.id  # Track who created
        )
        db.add(config_entry)
    
    db.commit()
    
    return {"message": f"{mode} configuration updated successfully"}

@router.get("/prompts/{mode}")
async def get_prompt_config(
    mode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prompt configuration for a specific mode (most recent manager config)"""
    # Get the most recent config for this mode (manager-created only)
    config = db.query(LLMConfig).filter(
        LLMConfig.name == f"{mode}_mode"
    ).order_by(LLMConfig.updated_at.desc()).first()
    
    if not config:
        # Return default
        return {
            "system": DEFAULT_PROMPTS[mode],
            "temperature": 0.7 if mode == "practice" else 0.5,
            "maxTokens": 2048 if mode == "practice" else 1024
        }
    
    return {
        "system": config.system_prompt,
        "temperature": config.temperature,
        "maxTokens": config.max_tokens
    }

@router.delete("/prompts/{mode}")
async def delete_prompt_config(
    mode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete saved prompt config and revert to defaults"""
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete configs")
    
    # Get the most recent config for this mode
    config = db.query(LLMConfig).filter(
        LLMConfig.name == f"{mode}_mode"
    ).order_by(LLMConfig.updated_at.desc()).first()
    
    if config:
        db.delete(config)
        db.commit()
        return {"message": f"{mode} configuration reset to default"}
    
    return {"message": "No custom configuration found"}

# Admin API Key Management - User-Friendly for Non-Technical Manager

@router.get("/providers/status", response_model=List[ProviderStatus])
async def get_providers_status(
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of all providers including API key availability"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view provider status")
    
    providers_status = []
    
    # Check available providers (Ollama is always available if running)
    available_providers = multi_llm_manager.get_available_providers()
    available_names = [p["name"] for p in available_providers]
    
    # List of all possible providers
    all_providers = [
        {"name": "ollama", "type": "local", "requires_key": False},
        {"name": "openai", "type": "cloud", "requires_key": True},
        {"name": "anthropic", "type": "cloud", "requires_key": True},
        {"name": "google", "type": "cloud", "requires_key": True},
        {"name": "cohere", "type": "cloud", "requires_key": True},
    ]
    
    for provider_info in all_providers:
        name = provider_info["name"]
        has_key = False
        
        # Check if provider has API key
        if not provider_info["requires_key"]:
            has_key = True  # Local providers don't need keys
        else:
            # Check if API key is available
            has_key = multi_llm_manager._has_api_key(name)
        
        providers_status.append(ProviderStatus(
            name=name,
            type=provider_info["type"],
            is_available=name in available_names,
            has_api_key=has_key,
            is_active=name == multi_llm_manager.active_provider,
            info=next((p["info"] for p in available_providers if p["name"] == name), {})
        ))
    
    return providers_status

@router.post("/providers/api-key", response_model=APIKeyResponse)
async def add_update_api_key(
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user)
):
    """Add or update API key for a cloud provider - Manager-friendly!"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage API keys")
    
    provider_name = api_key_data.provider_name.lower()
    
    # Validate provider name
    valid_providers = ["openai", "anthropic", "google", "cohere"]
    if provider_name not in valid_providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid provider. Supported: {', '.join(valid_providers)}"
        )
    
    # Basic API key validation
    if not api_key_data.api_key or len(api_key_data.api_key.strip()) < 10:
        raise HTTPException(status_code=400, detail="API key appears to be invalid")
    
    try:
        # Add the API key to the multi_llm_manager
        success = multi_llm_manager.add_api_key(provider_name, api_key_data.api_key.strip())
        
        if success:
            return APIKeyResponse(
                provider_name=provider_name,
                has_key=True,
                key_length=len(api_key_data.api_key.strip())
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to add API key")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding API key: {str(e)}")

@router.delete("/providers/{provider_name}/api-key")
async def remove_api_key(
    provider_name: str,
    current_user: User = Depends(get_current_user)
):
    """Remove API key for a provider"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage API keys")
    
    provider_name = provider_name.lower()
    
    try:
        success = multi_llm_manager.remove_api_key(provider_name)
        
        if success:
            return {"message": f"API key removed for {provider_name}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove API key")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing API key: {str(e)}")

@router.post("/models/deactivate")
async def toggle_model_activation(
    deactivation_data: ModelDeactivationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Deactivate or activate a specific model"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can deactivate models")
    
    try:
        success = multi_llm_manager.deactivate_model(
            model_key=deactivation_data.model_key,
            deactivated=deactivation_data.is_deactivated
        )
        
        if success:
            action = "deactivated" if deactivation_data.is_deactivated else "activated"
            return {"message": f"Model {deactivation_data.model_key} has been {action}"}
        else:
            raise HTTPException(status_code=400, detail="Model not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating model status: {str(e)}")