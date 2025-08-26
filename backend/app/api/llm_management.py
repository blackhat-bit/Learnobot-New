# app/api/llm_management.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.ai.multi_llm_manager import multi_llm_manager
from app.schemas.llm_config import (
    LLMProviderInfo, LLMConfigCreate, LLMConfigUpdate,
    ProviderComparison, SystemPromptUpdate
)

router = APIRouter()

@router.get("/providers", response_model=List[LLMProviderInfo])
async def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """Get list of all available LLM providers"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return multi_llm_manager.get_available_providers()

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
    
    # Save to database
    config_entry = db.query(LLMConfig).filter(
        LLMConfig.name == f"{mode}_mode",
        LLMConfig.created_by == current_user.id
    ).first()
    
    if config_entry:
        config_entry.system_prompt = config.system
        config_entry.temperature = config.temperature
        config_entry.max_tokens = config.maxTokens
        config_entry.updated_at = datetime.utcnow()
    else:
        config_entry = LLMConfig(
            provider_id=1,  # Default provider
            name=f"{mode}_mode",
            model=multi_llm_manager.active_provider,
            temperature=config.temperature,
            max_tokens=config.maxTokens,
            system_prompt=config.system,
            created_by=current_user.id
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
    """Get prompt configuration for a specific mode"""
    config = db.query(LLMConfig).filter(
        LLMConfig.name == f"{mode}_mode",
        LLMConfig.created_by == current_user.id
    ).first()
    
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