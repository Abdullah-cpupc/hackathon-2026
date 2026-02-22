from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routes import auth_router
from .company_routes import company_router
from .widget_routes import widget_router
from .ai_routes import ai_router
from .config import settings

# Create FastAPI app
app = FastAPI(
    title="AI Chat Backend",
    description="Backend API for AI Chat Application",
    version="1.0.0"
)

# Add CORS middleware - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(widget_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")

# Mount static files for uploads
import os
uploads_dir = "uploads"
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
def read_root():
    return {"message": "AI Chat Backend API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Create database tables on startup (only if database is available)
@app.on_event("startup")
async def startup_event():
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.warning(f"⚠️  Warning: Could not connect to database: {e}")
        logger.warning("   The application will start but database operations will fail.")
        logger.warning("   Please ensure PostgreSQL is running and update your .env file.")
    
    # Log startup information
    logger.info(f"🚀 Application starting in {settings.environment} mode")
    logger.info(f"📡 Base URL: {settings.base_url}")
    logger.info(f"🔑 Gemini API key configured: {'Yes' if settings.google_api_key else 'No'}")
