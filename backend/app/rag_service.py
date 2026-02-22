"""
RAG Service for AI Chat Backend
This service handles ChromaDB operations and AI model interactions.
"""

import os
import asyncio
from typing import Optional, Dict, Any, List, Callable
import logging

from .utils import get_chroma_client, get_or_create_collection, add_documents_to_collection, collection_exists
from .scraper import WebsiteScraper
from .document_parser import DocumentParser
from .llm_service import ModelLoader, RAG_Bot_Local

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    """
    RAG Service for managing ChromaDB collections and AI interactions.
    Full implementation with website scraping and local LLM integration.
    """
    
    def __init__(self, db_directory: str = "./chroma_db"):
        self.db_directory = db_directory
        self.client = None
        self.collections = {}
        self.model_loader = None
        
        try:
            # Ensure ChromaDB directory exists
            os.makedirs(db_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = get_chroma_client(db_directory)
            
            # Initialize model loader (singleton) - this might fail if API key is not set
            try:
                self.model_loader = ModelLoader()
            except Exception as e:
                logger.warning(f"Failed to initialize ModelLoader: {e}. Will use mock pipeline.")
                self.model_loader = None
            
            logger.info(f"RAGService initialized with database directory: {db_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize RAGService: {e}")
            # Don't raise - allow app to start even if RAG service fails
            # The service will fail gracefully when used
    
    def get_collection(self, collection_name: str):
        """
        Get or create a ChromaDB collection.
        """
        try:
            collection = get_or_create_collection(
                self.client,
                collection_name,
                embedding_model_name=None  # Use ChromaDB default embedding function
            )
            return collection
        except Exception as e:
            logger.error(f"Error getting collection '{collection_name}': {e}")
            raise
    
    def get_response(self, collection_name: str, query: str, n_results: int = 5) -> str:
        """
        Get AI response for a query using the specified collection.
        """
        try:
            logger.info(f"🔧 RAG SERVICE - Getting response for collection: '{collection_name}'")
            logger.info(f"   📝 Query: '{query}'")
            logger.info(f"   📊 n_results: {n_results}")
            
            # Check if model loader is available
            if not self.model_loader:
                logger.warning("ModelLoader not initialized, attempting to initialize now...")
                try:
                    self.model_loader = ModelLoader()
                except Exception as e:
                    logger.error(f"Failed to initialize ModelLoader: {e}")
                    return "I apologize, but the AI service is not properly configured. Please check the Google API key configuration."
            
            # Get the Gemini model
            gemini_model = self.model_loader.get_model()
            logger.info(f"   🤖 Gemini model loaded: {type(gemini_model)}")
            
            # Create RAG bot for this collection
            rag_bot = RAG_Bot_Local(
                collection_name=collection_name,
                gemini_model=gemini_model,
                db_directory=self.db_directory
            )
            logger.info(f"   🎯 RAG bot created for collection: '{collection_name}'")
            
            # Get AI response
            response = rag_bot.answer(query, n_results=n_results)
            logger.info(f"   ✅ RAG response generated successfully")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ RAG SERVICE ERROR: {e}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"
    
    def delete_collection(self, collection_name: str):
        """
        Delete a ChromaDB collection.
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            raise
    
    async def scrape_website(
        self, 
        urls: List[str], 
        collection_name: str,
        progress_callback: Optional[Callable[[str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """
        Scrape website URLs and populate the ChromaDB collection.
        
        Args:
            urls: List of URLs to scrape
            collection_name: Name of the ChromaDB collection
            progress_callback: Optional callback function(message, details) for progress updates
        """
        try:
            if progress_callback:
                progress_callback("Analyzing your website...", {"step": "starting"})
            
            logger.info(f"Starting website scraping for collection '{collection_name}' with {len(urls)} URLs")
            
            # Initialize scraper
            scraper = WebsiteScraper(chunk_size=1000, max_depth=3, max_concurrent=5)
            
            # Create progress callback wrapper for scraper
            def scraper_progress_callback(url: str, url_index: int, url_total: int):
                """Wrapper to convert scraper callback format to our format."""
                if progress_callback:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    domain = parsed.netloc or url
                    progress_callback(
                        f"Reading page {url_index} of {url_total}: {domain}",
                        {
                            "step": "scraping",
                            "current_url": url,
                            "url_index": url_index,
                            "total_urls": url_total
                        }
                    )
            
            # Scrape URLs
            scrape_results = await scraper.scrape_urls(urls, progress_callback=scraper_progress_callback)
            
            if not scrape_results:
                logger.warning("No content was scraped from the provided URLs")
                return {
                    "status": "warning",
                    "message": "No content was found to scrape",
                    "documents_added": 0,
                    "urls_processed": len(urls),
                    "collection_name": collection_name
                }
            
            # Process content for ChromaDB
            if progress_callback:
                progress_callback("Organizing content...", {"step": "chunking", "pages_found": len(scrape_results)})
            
            ids, documents, metadatas = scraper.process_content_for_chromadb(scrape_results)

            # Check if chunking produced any documents
            if not documents:
                logger.warning(f"⚠️ Scraper found {len(scrape_results)} pages but chunking produced 0 documents!")
                logger.warning("This likely indicates a bug in the chunking logic.")
                # Log the raw scrape results for debugging
                for result in scrape_results[:3]:  # Log first 3
                    logger.warning(f"   Page: {result.get('url')}")
                    logger.warning(f"   Title: {result.get('title')}")
                    logger.warning(f"   Markdown length: {len(result.get('markdown', ''))}")
                    logger.warning(f"   Markdown preview: {result.get('markdown', '')[:200]}")
                return {
                    "status": "warning",
                    "message": f"Found {len(scrape_results)} pages but could not extract text chunks",
                    "documents_added": 0,
                    "urls_processed": len(urls),
                    "collection_name": collection_name
                }

            # Delete and recreate collection to clear old documents
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"✅ Cleared existing collection '{collection_name}'")
            except ValueError as e:
                # Collection doesn't exist - this is fine
                logger.info(f"Collection '{collection_name}' doesn't exist yet, creating new")
            except Exception as e:
                # Log other errors but continue
                logger.warning(f"⚠️ Error deleting collection '{collection_name}': {e}")

            collection = self.get_collection(collection_name)

            # Add documents to collection
            if progress_callback:
                progress_callback(
                    f"Saving {len(documents)} chunks to knowledge base...",
                    {"step": "adding_to_db", "chunks_count": len(documents)}
                )
            
            await add_documents_to_collection(
                collection=collection,
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                batch_size=100
            )
            
            logger.info(f"Successfully added {len(documents)} documents to collection '{collection_name}'")
            
            return {
                "status": "success",
                "documents_added": len(documents),
                "urls_processed": len(urls),
                "collection_name": collection_name,
                "chunks_created": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error scraping website for collection '{collection_name}': {e}")
            return {
                "status": "error",
                "message": str(e),
                "documents_added": 0,
                "urls_processed": len(urls),
                "collection_name": collection_name
            }
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a specific collection.
        This method is optimized to avoid blocking operations and model downloads.
        """
        try:
            # Check if collection exists first without initializing embedding function
            # This is a lightweight check that doesn't trigger ONNX model downloads
            if not collection_exists(self.client, collection_name):
                return {
                    "collection_name": collection_name,
                    "document_count": 0,
                    "status": "not_found"
                }
            
            # Only get the collection if it exists to avoid initialization overhead
            # This will initialize the embedding function, but only if collection exists
            collection = self.get_collection(collection_name)
            count = collection.count()
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "status": "active"
            }
        except Exception as e:
            # Don't log as error for status checks - it's expected during building
            logger.debug(f"Error getting collection info for '{collection_name}': {e}")
            return {
                "collection_name": collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    async def process_documents(
        self,
        file_paths: List[str],
        file_types: List[str],
        filenames: List[str],
        collection_name: str,
        progress_callback: Optional[Callable[[str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded documents and populate the ChromaDB collection.
        
        Args:
            file_paths: List of file paths to process
            file_types: List of MIME types corresponding to file_paths
            filenames: List of original filenames
            collection_name: Name of the ChromaDB collection
            progress_callback: Optional callback function(message, details) for progress updates
            
        Returns:
            Dictionary with status and processing results
        """
        try:
            if progress_callback:
                progress_callback(
                    f"Adding your documents... ({len(file_paths)} files)",
                    {"step": "processing_files", "file_count": len(file_paths)}
                )
            
            logger.info(f"Starting document processing for collection '{collection_name}' with {len(file_paths)} files")
            
            # Initialize document parser
            parser = DocumentParser(chunk_size=1000, max_concurrent=5)
            
            # Parse documents in parallel
            parse_results = await parser.parse_files(file_paths, file_types, filenames)
            
            if not parse_results:
                logger.warning("No content was extracted from the provided files")
                return {
                    "status": "warning",
                    "message": "No content was found in the files",
                    "documents_added": 0,
                    "files_processed": len(file_paths),
                    "collection_name": collection_name
                }
            
            # Process content for ChromaDB
            if progress_callback:
                progress_callback(
                    "Organizing document content...",
                    {"step": "chunking_files", "files_processed": len(parse_results)}
                )
            
            ids, documents, metadatas = parser.process_content_for_chromadb(parse_results)
            
            # Get or create collection
            collection = self.get_collection(collection_name)
            
            # Add documents to collection
            if progress_callback:
                progress_callback(
                    f"Saving {len(documents)} document chunks to knowledge base...",
                    {"step": "adding_files_to_db", "chunks_count": len(documents)}
                )
            
            await add_documents_to_collection(
                collection=collection,
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                batch_size=100
            )
            
            logger.info(f"Successfully added {len(documents)} document chunks to collection '{collection_name}'")
            
            return {
                "status": "success",
                "documents_added": len(documents),
                "files_processed": len(file_paths),
                "collection_name": collection_name,
                "chunks_created": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error processing documents for collection '{collection_name}': {e}")
            return {
                "status": "error",
                "message": str(e),
                "documents_added": 0,
                "files_processed": len(file_paths),
                "collection_name": collection_name
            }
