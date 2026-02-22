from pydantic import BaseModel, EmailStr, validator, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Company schemas
class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website_urls: List[str]
    description: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website_urls: Optional[List[str]] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: int
    owner_id: int
    ai_enabled: bool
    ai_collection_name: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    ai_build_status: Optional[str] = None
    ai_error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Knowledge Base File schemas
class KnowledgeBaseFileBase(BaseModel):
    description: Optional[str] = None

class KnowledgeBaseFileCreate(KnowledgeBaseFileBase):
    pass

class KnowledgeBaseFileResponse(KnowledgeBaseFileBase):
    id: int
    company_id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    uploaded_by_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Company with files response
class CompanyWithFilesResponse(CompanyResponse):
    knowledge_base_files: List[KnowledgeBaseFileResponse] = []
    
    class Config:
        from_attributes = True

# Widget schemas
class WidgetBase(BaseModel):
    name: str
    position: str  # 'bottom-left' or 'bottom-right'
    minimized_shape: str  # 'circle' or 'pill'
    minimized_bg_color: str  # Hex color
    maximized_style: str  # 'solid' or 'blurred'
    system_bubble_bg_color: str  # Hex color
    user_bubble_bg_color: str  # Hex color
    is_active: bool = True

class WidgetCreate(WidgetBase):
    pass

class WidgetUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    minimized_shape: Optional[str] = None
    minimized_bg_color: Optional[str] = None
    maximized_style: Optional[str] = None
    system_bubble_bg_color: Optional[str] = None
    user_bubble_bg_color: Optional[str] = None
    is_active: Optional[bool] = None

class WidgetResponse(WidgetBase):
    id: int
    company_id: int
    widget_id: str
    api_key: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    @field_validator('allowed_domains', mode='before')
    @classmethod
    def parse_allowed_domains(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
    
    model_config = {"from_attributes": True}

class WidgetToggleResponse(BaseModel):
    message: str
    is_active: bool

# AI schemas
class AIBuildRequest(BaseModel):
    website_urls: Optional[List[str]] = None

class AIBuildResponse(BaseModel):
    message: str
    company_id: int
    collection_name: str
    status: str

class AIScrapeRequest(BaseModel):
    website_urls: Optional[List[str]] = None

class AIScrapeResponse(BaseModel):
    message: str
    company_id: int
    status: str

class AIBuildProgress(BaseModel):
    current_step: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class AIStatusResponse(BaseModel):
    company_id: int
    ai_enabled: bool
    ai_build_status: Optional[str]
    collection_name: Optional[str]
    last_scraped_at: Optional[datetime]
    document_count: int
    error_message: Optional[str]
    progress: Optional[AIBuildProgress] = None

class AIChatRequest(BaseModel):
    message: str
    n_results: int = 5

class AIChatResponse(BaseModel):
    message: str
    response: str
    company_id: int
    timestamp: datetime
