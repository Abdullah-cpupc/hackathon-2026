from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database import get_db, User, Company, KnowledgeBaseFile, SessionLocal
from .schemas import (
    CompanyCreate, CompanyResponse, CompanyUpdate, CompanyWithFilesResponse,
    KnowledgeBaseFileResponse
)
from .auth import get_current_user
from .config import settings
from .rag_service import RAGService

# Create company router
company_router = APIRouter(prefix="/companies", tags=["companies"])

# Initialize RAG service
rag_service = RAGService()

# File upload settings
UPLOAD_DIR = "uploads"
LOGO_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "logos")
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/json"
}
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg", 
    "image/png",
    "image/gif",
    "image/webp"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOGO_SIZE = 5 * 1024 * 1024  # 5MB for logos

# Ensure upload directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOGO_UPLOAD_DIR, exist_ok=True)

# Company routes
@company_router.post("/", response_model=CompanyResponse)
def create_company(
    company: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate website URLs
    if not company.website_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one website URL is required"
        )
    
    # Create company
    db_company = Company(
        name=company.name,
        address=company.address,
        phone=company.phone,
        website_urls=json.dumps(company.website_urls),
        description=company.description,
        industry=company.industry,
        logo_url=company.logo_url,
        owner_id=current_user.id
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    # Convert website_urls back to list for response
    db_company.website_urls = json.loads(db_company.website_urls)
    return db_company

@company_router.get("/", response_model=List[CompanyResponse])
def get_user_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    companies = db.query(Company).filter(Company.owner_id == current_user.id).all()
    
    # Convert website_urls from JSON string to list
    for company in companies:
        company.website_urls = json.loads(company.website_urls)
    
    return companies

@company_router.get("/{company_id}", response_model=CompanyWithFilesResponse)
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Convert website_urls from JSON string to list
    company.website_urls = json.loads(company.website_urls)
    return company

@company_router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Update fields
    update_data = company_update.dict(exclude_unset=True)
    
    if "website_urls" in update_data:
        if not update_data["website_urls"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one website URL is required"
            )
        update_data["website_urls"] = json.dumps(update_data["website_urls"])
    
    for field, value in update_data.items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    
    # Convert website_urls back to list for response
    company.website_urls = json.loads(company.website_urls)
    return company

@company_router.delete("/{company_id}")
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Delete associated files
    files = db.query(KnowledgeBaseFile).filter(KnowledgeBaseFile.company_id == company_id).all()
    for file in files:
        # Delete physical file
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        db.delete(file)
    
    db.delete(company)
    db.commit()
    
    return {"message": "Company deleted successfully"}

# File upload routes
@company_router.post("/{company_id}/files", response_model=KnowledgeBaseFileResponse)
async def upload_file(
    company_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
        )
    
    # Read file content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Create database record
    db_file = KnowledgeBaseFile(
        company_id=company_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        description=description,
        uploaded_by_id=current_user.id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # If company has AI enabled and collection exists, process the file in background
    if company.ai_enabled and company.ai_collection_name:
        background_tasks.add_task(
            process_file_background_task,
            company_id,
            db_file.id,
            file_path,
            file.content_type,
            file.filename,
            company.ai_collection_name
        )
    
    return db_file

@company_router.get("/{company_id}/files", response_model=List[KnowledgeBaseFileResponse])
def get_company_files(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    files = db.query(KnowledgeBaseFile).filter(KnowledgeBaseFile.company_id == company_id).all()
    return files

@company_router.delete("/{company_id}/files/{file_id}")
def delete_file(
    company_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Get file
    file = db.query(KnowledgeBaseFile).filter(
        KnowledgeBaseFile.id == file_id,
        KnowledgeBaseFile.company_id == company_id
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Delete physical file
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Delete database record
    db.delete(file)
    db.commit()
    
    return {"message": "File deleted successfully"}

# Logo upload route
@company_router.post("/{company_id}/logo")
async def upload_logo(
    company_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read file content to check size
    content = await file.read()
    if len(content) > MAX_LOGO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logo size exceeds maximum allowed size of {MAX_LOGO_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"logo_{company_id}_{uuid.uuid4()}{file_extension}"
    
    # Save file locally
    file_path = os.path.join(LOGO_UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    # Update company with logo URL - use configurable base URL
    logo_url = f"{settings.base_url}/uploads/logos/{unique_filename}"
    
    company.logo_url = logo_url
    db.commit()
    
    return {"message": "Logo uploaded successfully", "logo_url": company.logo_url}

# Delete logo route
@company_router.delete("/{company_id}/logo")
def delete_logo(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Delete physical file if it exists
    if company.logo_url:
        # Extract filename from URL
        filename = os.path.basename(company.logo_url)
        file_path = os.path.join(LOGO_UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Clear logo URL from database
        company.logo_url = None
        db.commit()
    
    return {"message": "Logo deleted successfully"}

@company_router.post("/{company_id}/files/process")
async def process_company_files(
    company_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process all uploaded files for a company and add them to the ChromaDB collection.
    """
    # Verify company exists and belongs to user
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.owner_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    if not company.ai_collection_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI must be built first before processing files"
        )
    
    # Get all files for the company
    files = db.query(KnowledgeBaseFile).filter(
        KnowledgeBaseFile.company_id == company_id
    ).all()
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found for this company"
        )
    
    # Start background task to process all files
    background_tasks.add_task(
        process_files_background_task,
        company_id,
        company.ai_collection_name
    )
    
    return {
        "message": "File processing started",
        "files_count": len(files),
        "company_id": company_id
    }

# Background task functions
async def process_file_background_task(
    company_id: int,
    file_id: int,
    file_path: str,
    file_type: str,
    filename: str,
    collection_name: str
):
    """Background task to process a single uploaded file."""
    db = SessionLocal()
    try:
        logger.info(f"Processing file {filename} for company {company_id}")
        
        # Process the file using local file path
        result = await rag_service.process_documents(
            file_paths=[file_path],
            file_types=[file_type],
            filenames=[filename],
            collection_name=collection_name
        )
        
        if result["status"] == "success":
            logger.info(f"Successfully processed file {filename}. Added {result['documents_added']} chunks.")
        else:
            logger.error(f"Failed to process file {filename}: {result.get('message', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Error in process_file_background_task for file {file_id}: {e}")
    finally:
        db.close()

async def process_files_background_task(company_id: int, collection_name: str):
    """Background task to process all uploaded files for a company."""
    db = SessionLocal()
    try:
        # Get all files for the company
        files = db.query(KnowledgeBaseFile).filter(
            KnowledgeBaseFile.company_id == company_id
        ).all()
        
        if not files:
            logger.warning(f"No files found for company {company_id}")
            return
        
        logger.info(f"Processing {len(files)} files for company {company_id}")
        
        # Prepare file data from local filesystem
        file_paths = [file.file_path for file in files]
        file_types = [file.file_type for file in files]
        filenames = [file.original_filename for file in files]
        
        # Process all files in parallel
        result = await rag_service.process_documents(
            file_paths=file_paths,
            file_types=file_types,
            filenames=filenames,
            collection_name=collection_name
        )
        
        if result["status"] == "success":
            logger.info(f"Successfully processed {result['files_processed']} files. Added {result['documents_added']} chunks.")
        else:
            logger.error(f"Failed to process files: {result.get('message', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Error in process_files_background_task for company {company_id}: {e}")
    finally:
        db.close()

# Export router
__all__ = ["company_router"]
