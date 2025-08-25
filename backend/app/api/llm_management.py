from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_active_user
from app.models.user import User
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigBase,
    LLMConfigSummary,
    LLMConfigDetail,
    LLMUsageStats,
    LLMPerformanceMetrics,
    LLMTestRequest,
    LLMTestResult
)

router = APIRouter()


@router.post("/configs", response_model=LLMConfigDetail, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    config_data: LLMConfigCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new LLM configuration (Admin only)."""
    
    # Check if name already exists
    existing_config = db.query(LLMConfig).filter(LLMConfig.name == config_data.name).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration with this name already exists"
        )
    
    db_config = LLMConfig(**config_data.dict())
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.get("/configs", response_model=List[LLMConfigSummary])
async def get_llm_configs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    provider: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get LLM configurations."""
    
    query = db.query(LLMConfig)
    
    if provider:
        query = query.filter(LLMConfig.provider == provider)
    
    if is_active is not None:
        query = query.filter(LLMConfig.is_active == is_active)
    
    configs = query.order_by(desc(LLMConfig.created_at)).offset(skip).limit(limit).all()
    
    return configs


@router.get("/configs/{config_id}", response_model=LLMConfigDetail)
async def get_llm_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific LLM configuration."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    return config


@router.put("/configs/{config_id}", response_model=LLMConfigDetail)
async def update_llm_config(
    config_id: int,
    config_data: LLMConfigUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update an LLM configuration (Admin only)."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    # Check if new name conflicts with existing config
    if config_data.name and config_data.name != config.name:
        existing_config = db.query(LLMConfig).filter(
            LLMConfig.name == config_data.name,
            LLMConfig.id != config_id
        ).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration with this name already exists"
            )
    
    # Update fields if provided
    for field, value in config_data.dict(exclude_unset=True).items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return config


@router.delete("/configs/{config_id}")
async def delete_llm_config(
    config_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an LLM configuration (Admin only)."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    if config.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default configuration"
        )
    
    db.delete(config)
    db.commit()
    
    return {"message": "LLM configuration deleted successfully"}


@router.post("/configs/{config_id}/set-default")
async def set_default_config(
    config_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Set an LLM configuration as default (Admin only)."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    if not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set inactive configuration as default"
        )
    
    # Remove default flag from all configs
    db.query(LLMConfig).update({"is_default": False})
    
    # Set this config as default
    config.is_default = True
    
    db.commit()
    
    return {"message": "Default configuration updated successfully"}


@router.post("/configs/{config_id}/test", response_model=LLMTestResult)
async def test_llm_config(
    config_id: int,
    test_data: LLMTestRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Test an LLM configuration (Admin only)."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    # TODO: Implement actual LLM testing logic
    # This would involve making a test request to the LLM with the given configuration
    
    from datetime import datetime
    import time
    
    # Placeholder test result
    test_result = LLMTestResult(
        config_id=config_id,
        test_prompt=test_data.test_prompt,
        response="This is a test response",  # Would be actual LLM response
        response_time=0.5,  # Would be actual response time
        tokens_used=25,  # Would be actual token count
        success=True,
        error_message=None,
        quality_score=0.85,  # Would be calculated quality score
        timestamp=datetime.utcnow()
    )
    
    return test_result


@router.get("/configs/{config_id}/usage", response_model=LLMUsageStats)
async def get_config_usage(
    config_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get usage statistics for an LLM configuration (Admin only)."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    # TODO: Implement actual usage statistics from logs/database
    # This would query usage logs for the specified time period
    
    from datetime import datetime, timedelta
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Placeholder usage stats
    usage_stats = LLMUsageStats(
        config_id=config_id,
        config_name=config.name,
        total_requests=1250,
        successful_requests=1200,
        failed_requests=50,
        total_tokens_used=75000,
        average_response_time=0.8,
        cost_estimate=15.0 if config.cost_per_token else None,
        period_start=start_date,
        period_end=end_date
    )
    
    return usage_stats


@router.get("/configs/{config_id}/performance", response_model=LLMPerformanceMetrics)
async def get_config_performance(
    config_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get performance metrics for an LLM configuration (Admin only)."""
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM configuration not found"
        )
    
    # TODO: Implement actual performance metrics calculation
    # This would aggregate performance data from usage logs
    
    # Placeholder performance metrics
    performance_metrics = LLMPerformanceMetrics(
        config_id=config_id,
        response_quality_score=config.response_quality_score or 0.85,
        user_satisfaction_score=4.2,
        error_rate=0.04,  # 4% error rate
        uptime_percentage=config.uptime_percentage or 99.5,
        average_latency=config.average_response_time or 0.8,
        tokens_per_second=125.0
    )
    
    return performance_metrics


@router.get("/dashboard")
async def get_llm_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get LLM management dashboard statistics (Admin only)."""
    
    # Get basic counts
    total_configs = db.query(LLMConfig).count()
    active_configs = db.query(LLMConfig).filter(LLMConfig.is_active == True).count()
    experimental_configs = db.query(LLMConfig).filter(LLMConfig.is_experimental == True).count()
    
    # Get provider distribution
    provider_counts = {}
    configs = db.query(LLMConfig).all()
    for config in configs:
        provider_counts[config.provider] = provider_counts.get(config.provider, 0) + 1
    
    # Get default config
    default_config = db.query(LLMConfig).filter(LLMConfig.is_default == True).first()
    
    return {
        "total_configs": total_configs,
        "active_configs": active_configs,
        "experimental_configs": experimental_configs,
        "provider_distribution": provider_counts,
        "default_config": {
            "id": default_config.id,
            "name": default_config.name,
            "provider": default_config.provider,
            "model_name": default_config.model_name
        } if default_config else None
    }
