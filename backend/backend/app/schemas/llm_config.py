from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator


class LLMConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    provider: str
    model_name: str
    api_endpoint: Optional[str] = None
    api_key_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_prompt: Optional[str] = None
    context_window: int = 4096
    max_requests_per_minute: int = 60
    max_requests_per_day: int = 1000
    cost_per_token: Optional[float] = None
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    supports_fine_tuning: bool = False
    use_cases: Optional[List[str]] = None
    subject_specializations: Optional[List[str]] = None
    content_filter_enabled: bool = True
    safety_level: str = "medium"
    custom_parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        if len(v) > 100:
            raise ValueError('Name must be no more than 100 characters')
        return v.strip()

    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'anthropic', 'huggingface', 'cohere', 'palm', 'local']
        if v.lower() not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        return v.lower()

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0.0 or v > 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v < 1 or v > 100000:
            raise ValueError('Max tokens must be between 1 and 100,000')
        return v

    @validator('top_p')
    def validate_top_p(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Top-p must be between 0.0 and 1.0')
        return v

    @validator('safety_level')
    def validate_safety_level(cls, v):
        if v not in ['low', 'medium', 'high', 'strict']:
            raise ValueError('Safety level must be low, medium, high, or strict')
        return v


class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    system_prompt: Optional[str] = None
    max_requests_per_minute: Optional[int] = None
    max_requests_per_day: Optional[int] = None
    cost_per_token: Optional[float] = None
    use_cases: Optional[List[str]] = None
    subject_specializations: Optional[List[str]] = None
    content_filter_enabled: Optional[bool] = None
    safety_level: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class LLMConfigBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    context_window: int
    is_active: bool
    is_default: bool
    is_experimental: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LLMConfigSummary(BaseModel):
    id: int
    name: str
    provider: str
    model_name: str
    is_active: bool
    is_default: bool
    use_cases: Optional[List[str]] = None
    subject_specializations: Optional[List[str]] = None

    class Config:
        from_attributes = True


class LLMConfigDetail(LLMConfigBase):
    api_endpoint: Optional[str] = None
    api_key_name: Optional[str] = None
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    system_prompt: Optional[str] = None
    max_requests_per_minute: int
    max_requests_per_day: int
    cost_per_token: Optional[float] = None
    supports_function_calling: bool
    supports_vision: bool
    supports_streaming: bool
    supports_fine_tuning: bool
    use_cases: Optional[List[str]] = None
    subject_specializations: Optional[List[str]] = None
    response_quality_score: Optional[float] = None
    average_response_time: Optional[float] = None
    uptime_percentage: Optional[float] = None
    content_filter_enabled: bool
    safety_level: str
    custom_parameters: Optional[Dict[str, Any]] = None
    preprocessing_config: Optional[Dict[str, Any]] = None
    postprocessing_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    last_used_at: Optional[datetime] = None


# LLM Usage and Analytics schemas
class LLMUsageStats(BaseModel):
    config_id: int
    config_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens_used: int
    average_response_time: float
    cost_estimate: Optional[float] = None
    period_start: datetime
    period_end: datetime


class LLMPerformanceMetrics(BaseModel):
    config_id: int
    response_quality_score: Optional[float] = None
    user_satisfaction_score: Optional[float] = None
    error_rate: float
    uptime_percentage: float
    average_latency: float
    tokens_per_second: float


# LLM Testing schemas
class LLMTestRequest(BaseModel):
    config_id: int
    test_prompt: str
    expected_behavior: Optional[str] = None
    test_parameters: Optional[Dict[str, Any]] = None


class LLMTestResult(BaseModel):
    config_id: int
    test_prompt: str
    response: str
    response_time: float
    tokens_used: int
    success: bool
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    timestamp: datetime
