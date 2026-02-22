from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Tuple
import json
import uuid
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database import get_db, User, Company, Widget, KnowledgeBaseFile
from .auth import get_current_user
from .schemas import (
    AIBuildRequest, AIBuildResponse, AIChatRequest, AIChatResponse,
    AIScrapeRequest, AIScrapeResponse, AIStatusResponse
)
from .rag_service import RAGService

# Create AI router
ai_router = APIRouter(prefix="/ai", tags=["ai"])

# Initialize RAG service
rag_service = RAGService()

@ai_router.post("/build/{company_id}", response_model=AIBuildResponse)
def build_ai_for_company(
    company_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize AI for a company by building the knowledge base.
    This will scrape the company's website and create a ChromaDB collection.
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
    
    # Check if company has website URLs
    website_urls = json.loads(company.website_urls) if company.website_urls else []
    if not website_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company must have at least one website URL to build AI"
        )
    
    # Check if AI is already being built
    if company.ai_build_status == 'building':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI is already being built for this company"
        )
    
    # Generate unique collection name
    collection_name = f"company_{company_id}_{company.name.lower().replace(' ', '_')}"
    
    # Update company status
    company.ai_build_status = 'building'
    company.ai_collection_name = collection_name
    company.ai_error_message = None
    db.commit()
    
    # Start background task to build AI
    background_tasks.add_task(
        build_ai_background_task,
        company_id,
        website_urls,
        collection_name
    )
    
    return AIBuildResponse(
        message="AI build started",
        company_id=company_id,
        collection_name=collection_name,
        status="building"
    )

@ai_router.post("/scrape/{company_id}", response_model=AIScrapeResponse)
def scrape_company_website(
    company_id: int,
    scrape_request: AIScrapeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Re-scrape the company's website to update the knowledge base.
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
            detail="AI must be built first before re-scraping"
        )
    
    # Update status
    company.ai_build_status = 'building'
    company.ai_error_message = None
    db.commit()
    
    # Get website URLs from request or use company's default URLs
    website_urls = scrape_request.website_urls or json.loads(company.website_urls)
    
    # Start background task to re-scrape
    background_tasks.add_task(
        scrape_website_background_task,
        company_id,
        website_urls,
        company.ai_collection_name
    )
    
    return AIScrapeResponse(
        message="Website scraping started",
        company_id=company_id,
        status="scraping"
    )

@ai_router.get("/status/{company_id}", response_model=AIStatusResponse)
async def get_ai_status(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current AI status for a company.
    This endpoint is optimized to be non-blocking and fast.
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
    
    # Get document count if collection exists - use non-blocking approach
    # Only try to get count if AI is ready to avoid triggering ChromaDB initialization
    # During 'building' status, skip collection access entirely to prevent blocking
    document_count = 0
    if company.ai_collection_name and company.ai_build_status == 'ready':
        try:
            # Use get_collection_info which checks existence first without initializing embedding function
            # This prevents ONNX model downloads during status checks
            collection_info = rag_service.get_collection_info(company.ai_collection_name)
            document_count = collection_info.get("document_count", 0)
        except Exception as e:
            # Silently fail - don't block the status endpoint
            # Collection might be in the process of being created or doesn't exist yet
            logger.debug(f"Could not get document count for collection '{company.ai_collection_name}': {e}")
            document_count = 0
    # If status is 'building', don't try to access collection at all to avoid blocking
    
    # Parse progress data if it exists
    progress = None
    if company.ai_build_progress:
        try:
            from .schemas import AIBuildProgress
            progress_data = json.loads(company.ai_build_progress)
            progress = AIBuildProgress(**progress_data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error parsing progress data for company {company_id}: {e}")
    
    return AIStatusResponse(
        company_id=company_id,
        ai_enabled=company.ai_enabled,
        ai_build_status=company.ai_build_status,
        collection_name=company.ai_collection_name,
        last_scraped_at=company.last_scraped_at,
        document_count=document_count,
        error_message=company.ai_error_message,
        progress=progress
    )

@ai_router.post("/chat/{company_id}", response_model=AIChatResponse)
def chat_with_ai(
    company_id: int,
    chat_request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the company's AI assistant.
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
    
    if not company.ai_enabled or company.ai_build_status != 'ready':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI is not ready for this company. Please build AI first."
        )
    
    if not company.ai_collection_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI collection not found"
        )
    
    try:
        logger.info(f"💬 CHAT REQUEST RECEIVED:")
        logger.info(f"   🏢 Company ID: {company_id}")
        logger.info(f"   👤 User: {current_user.username}")
        logger.info(f"   📝 Message: '{chat_request.message}'")
        logger.info(f"   🎯 Collection: '{company.ai_collection_name}'")
        logger.info(f"   📊 n_results: {chat_request.n_results}")
        
        # Get AI response
        response = rag_service.get_response(
            company.ai_collection_name,
            chat_request.message,
            n_results=chat_request.n_results
        )
        
        logger.info(f"✅ CHAT RESPONSE GENERATED:")
        logger.info(f"   📏 Response length: {len(response)} characters")
        logger.info(f"   📄 Response: {response}")
        
        return AIChatResponse(
            message=chat_request.message,
            response=response,
            company_id=company_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ CHAT ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting AI response: {str(e)}"
        )

def get_allowed_domains_for_widget(widget: Widget, company: Company) -> List[str]:
    """
    Get list of allowed domains for a widget.
    Uses widget's allowed_domains if available, otherwise falls back to company website URLs.
    
    Args:
        widget: Widget object
        company: Company object
        
    Returns:
        List of normalized domain names
    """
    allowed_domains = []
    
    # Try widget's allowed_domains first
    if widget.allowed_domains:
        try:
            allowed_domains = json.loads(widget.allowed_domains)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse widget allowed_domains: {widget.allowed_domains}")
    
    # Fallback to company website URLs if widget allowed_domains is empty
    if not allowed_domains and company.website_urls:
        try:
            website_urls = json.loads(company.website_urls)
            for url in website_urls:
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()
                    # Remove port number
                    if ':' in domain:
                        domain = domain.split(':')[0]
                    # Remove www. prefix for normalization
                    domain = domain.replace('www.', '')
                    if domain and domain not in allowed_domains:
                        allowed_domains.append(domain)
                except Exception as e:
                    logger.warning(f"Failed to parse company website URL {url}: {e}")
                    continue
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse company website_urls: {company.website_urls}")
    
    return allowed_domains

def validate_widget_domain(request: Request, widget: Widget, company: Company) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate that the request is coming from an allowed domain.
    Allows localhost/127.0.0.1 for development/preview purposes.
    
    Args:
        request: FastAPI Request object
        widget: Widget object with allowed_domains
        company: Company object with website_urls
        
    Returns:
        Tuple of (is_valid, source_domain, allowed_domains)
    """
    # Get origin or referer header
    origin = request.headers.get('origin')
    referer = request.headers.get('referer')
    
    # Try origin first (more reliable for CORS requests)
    source_url = origin or referer
    
    if not source_url:
        logger.warning("No origin or referer header found in widget request")
        allowed_domains = get_allowed_domains_for_widget(widget, company)
        return False, None, allowed_domains
    
    try:
        # Parse the source URL
        parsed_url = urlparse(source_url)
        source_domain = parsed_url.netloc.lower()
        
        # Remove port number for comparison
        if ':' in source_domain:
            source_domain = source_domain.split(':')[0]
        
        # Allow localhost and 127.0.0.1 for development/preview
        if source_domain in ['localhost', '127.0.0.1', '0.0.0.0']:
            logger.info(f"✅ Allowing localhost/127.0.0.1 domain: {source_domain}")
            allowed_domains = get_allowed_domains_for_widget(widget, company)
            return True, source_domain, allowed_domains
        
        # Get allowed domains
        allowed_domains = get_allowed_domains_for_widget(widget, company)
        
        # Normalize source domain (remove www. prefix and port)
        source_domain_normalized = source_domain.replace('www.', '')
        
        # Check if source domain matches any allowed domain
        for allowed_domain in allowed_domains:
            # Normalize allowed domain (remove www. prefix)
            allowed_domain_normalized = allowed_domain.replace('www.', '').lower()
            if source_domain_normalized == allowed_domain_normalized:
                logger.info(f"✅ Domain validated: {source_domain} matches {allowed_domain}")
                return True, source_domain, allowed_domains
        
        # Log detailed rejection information
        logger.warning(f"❌ Domain not allowed: {source_domain} (normalized: {source_domain_normalized})")
        logger.warning(f"   Allowed domains: {allowed_domains}")
        logger.warning(f"   Origin: {origin}")
        logger.warning(f"   Referer: {referer}")
        return False, source_domain, allowed_domains
        
    except Exception as e:
        logger.error(f"Error validating domain: {e}")
        allowed_domains = get_allowed_domains_for_widget(widget, company)
        return False, None, allowed_domains

@ai_router.post("/chat/{company_id}/widget", response_model=AIChatResponse)
def chat_with_ai_widget(
    company_id: int,
    chat_request: AIChatRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Chat with the company's AI assistant via widget (API key authentication).
    Validates that the request is coming from an allowed domain.
    """
    # Validate API key
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Find widget by API key and company
    widget = db.query(Widget).filter(
        Widget.company_id == company_id,
        Widget.api_key == x_api_key,
        Widget.is_active == True
    ).first()
    
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or widget not found"
        )
    
    # Verify company exists
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Validate domain (security check)
    is_valid, source_domain, allowed_domains = validate_widget_domain(request, widget, company)
    if not is_valid:
        origin = request.headers.get('origin', source_domain or 'Unknown')
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Domain not allowed for this widget. Request from '{origin}' is not in the allowed domains: {allowed_domains}. Please ensure the widget is embedded on a registered domain."
        )
    
    if not company.ai_enabled or company.ai_build_status != 'ready':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI is not ready for this company. Please build AI first."
        )
    
    if not company.ai_collection_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI collection not found"
        )
    
    try:
        # Log request origin for debugging
        origin = request.headers.get('origin', 'Not provided')
        referer = request.headers.get('referer', 'Not provided')
        logger.info(f"💬 WIDGET CHAT REQUEST RECEIVED:")
        logger.info(f"   🏢 Company ID: {company_id}")
        logger.info(f"   🔑 Widget ID: {widget.widget_id}")
        logger.info(f"   🌐 Origin: {origin}")
        logger.info(f"   🔗 Referer: {referer}")
        logger.info(f"   📝 Message: '{chat_request.message}'")
        logger.info(f"   🎯 Collection: '{company.ai_collection_name}'")
        logger.info(f"   📊 n_results: {chat_request.n_results}")
        
        # Get AI response
        response = rag_service.get_response(
            company.ai_collection_name,
            chat_request.message,
            n_results=chat_request.n_results
        )
        
        logger.info(f"✅ WIDGET CHAT RESPONSE GENERATED:")
        logger.info(f"   📏 Response length: {len(response)} characters")
        
        return AIChatResponse(
            message=chat_request.message,
            response=response,
            company_id=company_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ WIDGET CHAT ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting AI response: {str(e)}"
        )

@ai_router.delete("/disable/{company_id}")
def disable_ai_for_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable AI for a company and clean up resources.
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
    
    # Update company status
    company.ai_enabled = False
    company.ai_build_status = 'disabled'
    db.commit()
    
    # Clean up ChromaDB collection (optional - might want to keep for re-enabling)
    # rag_service.delete_collection(company.ai_collection_name)
    
    return {"message": "AI disabled successfully"}

def update_progress_in_db(db, company_id: int, message: str, details: Optional[Dict[str, Any]] = None):
    """Helper function to update progress in database."""
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            progress_data = {
                "current_step": details.get("step", "processing") if details else "processing",
                "message": message,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            company.ai_build_progress = json.dumps(progress_data)
            db.commit()
            db.refresh(company)
    except Exception as e:
        logger.error(f"Error updating progress in database: {e}")
        db.rollback()

# Background task functions
async def build_ai_background_task(company_id: int, website_urls: list, collection_name: str):
    """Background task to build AI for a company."""
    from sqlalchemy.orm import Session
    from .database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get company from database
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            logger.error(f"Company {company_id} not found during AI build")
            return
        
        logger.info(f"Starting AI build for company {company_id}")
        
        # Update status to building and clear progress
        company.ai_build_status = 'building'
        company.ai_error_message = None
        company.ai_build_progress = None
        db.commit()
        
        # Create progress callback
        def progress_callback(message: str, details: Optional[Dict[str, Any]] = None):
            update_progress_in_db(db, company_id, message, details)
        
        # Scrape website using RAG service
        scrape_result = await rag_service.scrape_website(
            website_urls, 
            collection_name,
            progress_callback=progress_callback
        )
        
        if scrape_result["status"] == "success":
            # Process uploaded files if any exist
            files = db.query(KnowledgeBaseFile).filter(
                KnowledgeBaseFile.company_id == company_id
            ).all()
            
            if files:
                logger.info(f"Processing {len(files)} uploaded files for company {company_id}")
                file_paths = [file.file_path for file in files]
                file_types = [file.file_type for file in files]
                filenames = [file.original_filename for file in files]
                
                file_result = await rag_service.process_documents(
                    file_paths=file_paths,
                    file_types=file_types,
                    filenames=filenames,
                    collection_name=collection_name,
                    progress_callback=progress_callback
                )
                
                if file_result["status"] == "success":
                    logger.info(f"Added {file_result['documents_added']} document chunks from files.")
                else:
                    logger.warning(f"Some files failed to process: {file_result.get('message', 'Unknown error')}")
            
            # Update company with success and clear progress
            company.ai_enabled = True
            company.ai_build_status = 'ready'
            company.last_scraped_at = datetime.utcnow()
            company.ai_error_message = None
            company.ai_build_progress = None
            total_docs = scrape_result['documents_added']
            if files:
                total_docs += file_result.get('documents_added', 0)
            logger.info(f"AI build completed successfully for company {company_id}. Added {total_docs} total documents.")
        else:
            # Update company with error and clear progress
            company.ai_build_status = 'failed'
            company.ai_error_message = scrape_result.get("message", "Unknown error during AI build")
            company.ai_build_progress = None
            logger.error(f"AI build failed for company {company_id}: {company.ai_error_message}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in build_ai_background_task for company {company_id}: {e}")
        # Update company with error
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.ai_build_status = 'failed'
                company.ai_error_message = str(e)
                company.ai_build_progress = None
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating company status in database: {db_error}")
    finally:
        db.close()

async def scrape_website_background_task(company_id: int, website_urls: list, collection_name: str):
    """Background task to scrape website and update AI."""
    from sqlalchemy.orm import Session
    from .database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get company from database
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            logger.error(f"Company {company_id} not found during re-scraping")
            return
        
        logger.info(f"Starting website re-scraping for company {company_id}")
        
        # Update status to building and clear progress
        company.ai_build_status = 'building'
        company.ai_error_message = None
        company.ai_build_progress = None
        db.commit()
        
        # Create progress callback
        def progress_callback(message: str, details: Optional[Dict[str, Any]] = None):
            update_progress_in_db(db, company_id, message, details)
        
        # Scrape website using RAG service
        scrape_result = await rag_service.scrape_website(
            website_urls, 
            collection_name,
            progress_callback=progress_callback
        )
        
        if scrape_result["status"] == "success":
            # Process uploaded files if any exist
            files = db.query(KnowledgeBaseFile).filter(
                KnowledgeBaseFile.company_id == company_id
            ).all()
            
            if files:
                logger.info(f"Processing {len(files)} uploaded files during re-scraping for company {company_id}")
                file_paths = [file.file_path for file in files]
                file_types = [file.file_type for file in files]
                filenames = [file.original_filename for file in files]
                
                file_result = await rag_service.process_documents(
                    file_paths=file_paths,
                    file_types=file_types,
                    filenames=filenames,
                    collection_name=collection_name,
                    progress_callback=progress_callback
                )
                
                if file_result["status"] == "success":
                    logger.info(f"Added {file_result['documents_added']} document chunks from files.")
                else:
                    logger.warning(f"Some files failed to process: {file_result.get('message', 'Unknown error')}")
            
            # Update company with success and clear progress
            company.ai_build_status = 'ready'
            company.last_scraped_at = datetime.utcnow()
            company.ai_error_message = None
            company.ai_build_progress = None
            total_docs = scrape_result['documents_added']
            if files:
                total_docs += file_result.get('documents_added', 0)
            logger.info(f"Website re-scraping completed successfully for company {company_id}. Added {total_docs} total documents.")
        else:
            # Update company with error and clear progress
            company.ai_build_status = 'failed'
            company.ai_error_message = scrape_result.get("message", "Unknown error during re-scraping")
            company.ai_build_progress = None
            logger.error(f"Website re-scraping failed for company {company_id}: {company.ai_error_message}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in scrape_website_background_task for company {company_id}: {e}")
        # Update company with error
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.ai_build_status = 'failed'
                company.ai_error_message = str(e)
                company.ai_build_progress = None
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating company status in database: {db_error}")
    finally:
        db.close()
