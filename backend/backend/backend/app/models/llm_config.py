from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.sql import func

from app.core.database import Base


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Model configuration
    provider = Column(String(50), nullable=False)  # openai, anthropic, huggingface, etc.
    model_name = Column(String(100), nullable=False)
    api_endpoint = Column(String(255), nullable=True)
    api_key_name = Column(String(100), nullable=True)  # Reference to env var name
    
    # Model parameters
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    top_p = Column(Float, default=1.0)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    
    # Context and behavior
    system_prompt = Column(Text, nullable=True)
    context_window = Column(Integer, default=4096)
    
    # Usage and limitations
    max_requests_per_minute = Column(Integer, default=60)
    max_requests_per_day = Column(Integer, default=1000)
    cost_per_token = Column(Float, nullable=True)
    
    # Features and capabilities
    supports_function_calling = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    supports_streaming = Column(Boolean, default=True)
    supports_fine_tuning = Column(Boolean, default=False)
    
    # Configuration for different use cases
    use_cases = Column(JSON, nullable=True)  # List of use cases: ["chat", "coding", "math", etc.]
    subject_specializations = Column(JSON, nullable=True)  # Subjects this model is good for
    
    # Quality and performance metrics
    response_quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    average_response_time = Column(Float, nullable=True)  # in seconds
    uptime_percentage = Column(Float, nullable=True)
    
    # Safety and moderation
    content_filter_enabled = Column(Boolean, default=True)
    safety_level = Column(String(20), default="medium")  # low, medium, high, strict
    
    # Status and availability
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    is_experimental = Column(Boolean, default=False)
    
    # Additional configuration
    custom_parameters = Column(JSON, nullable=True)  # Flexible additional params
    preprocessing_config = Column(JSON, nullable=True)  # Input preprocessing settings
    postprocessing_config = Column(JSON, nullable=True)  # Output postprocessing settings
    
    # Metadata
    tags = Column(JSON, nullable=True)  # List of tags for categorization
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<LLMConfig(id={self.id}, name='{self.name}', provider='{self.provider}', model='{self.model_name}')>"
