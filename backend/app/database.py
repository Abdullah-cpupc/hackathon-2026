from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from .config import settings

# Database setup
def get_database_url():
    """
    Get database URL from environment variable or settings.
    """
    # Check if DATABASE_URL is explicitly set
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Otherwise use the configured database_url from settings
    if settings.database_url:
        return settings.database_url
    
    # Fallback (shouldn't reach here, but just in case)
    raise ValueError("No database URL configured. Please set DATABASE_URL environment variable.")

# Create engine with connection pooling
# Use lazy initialization to avoid errors during import if database is not available
try:
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,  # 10 second timeout
        }
    )
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Could not initialize database engine: {e}")
    logger.error("Database operations will fail. Please check:")
    logger.error("  1. DATABASE_URL environment variable is set")
    logger.error("  2. PostgreSQL is running and accessible")
    # Create a dummy engine that will fail gracefully when used
    # This allows the app to start even if database is not available
    engine = None
    SessionLocal = None
else:
    # Only create SessionLocal if engine was successfully created
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to companies
    companies = relationship("Company", back_populates="owner")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    website_urls = Column(Text, nullable=False)  # JSON string of URLs
    description = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)  # URL/path to company logo
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI-related fields
    ai_enabled = Column(Boolean, nullable=False, default=False)
    ai_collection_name = Column(String, nullable=True)  # ChromaDB collection name
    last_scraped_at = Column(DateTime, nullable=True)
    ai_build_status = Column(String, nullable=True, default='not_started')  # not_started, building, ready, failed
    ai_error_message = Column(Text, nullable=True)
    ai_build_progress = Column(Text, nullable=True)  # JSON string of progress data
    
    # Relationships
    owner = relationship("User", back_populates="companies")
    knowledge_base_files = relationship("KnowledgeBaseFile", back_populates="company")

class KnowledgeBaseFile(Base):
    __tablename__ = "knowledge_base_files"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)  # MIME type
    description = Column(Text, nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="knowledge_base_files")
    uploaded_by = relationship("User")

class Widget(Base):
    __tablename__ = "widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    widget_id = Column(String, nullable=False, unique=True, index=True)  # Unique identifier for the widget
    position = Column(String, nullable=False)  # 'bottom-left' or 'bottom-right'
    minimized_shape = Column(String, nullable=False)  # 'circle' or 'pill'
    minimized_bg_color = Column(String, nullable=False)  # Hex color
    maximized_style = Column(String, nullable=False)  # 'solid' or 'blurred'
    system_bubble_bg_color = Column(String, nullable=False)  # Hex color
    user_bubble_bg_color = Column(String, nullable=False)  # Hex color
    is_active = Column(Boolean, nullable=False, default=True)
    api_key = Column(String, nullable=True, unique=True, index=True)  # API key for widget authentication
    allowed_domains = Column(Text, nullable=True)  # JSON string of allowed domains
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")

# Dependency to get database session
def get_db():
    if engine is None or SessionLocal is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Database engine is not initialized. Check database configuration.")
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not available. Please check database configuration and ensure DATABASE_URL is set."
        )
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
