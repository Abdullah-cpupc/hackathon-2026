"""
Document parsing module for processing uploaded files (PDFs, Word docs, TXT, JSON).
Processes documents in parallel and prepares them for ChromaDB ingestion.
"""

import os
import io
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import aiofiles
from more_itertools import batched

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import document parsing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. PDF parsing will be disabled.")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. Word document parsing will be disabled.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. Advanced PDF parsing will be disabled.")


async def parse_pdf(file_path: str) -> str:
    """
    Parse a PDF file and extract text content.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        raise ImportError("No PDF parsing library available. Please install PyPDF2 or pdfplumber.")
    
    text_content = []
    
    try:
        # Try pdfplumber first (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            def _read_pdfplumber(path):
                text_parts = []
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                return text_parts
            
            text_content = await asyncio.to_thread(_read_pdfplumber, file_path)
        # Fallback to PyPDF2
        elif PDF_AVAILABLE:
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # PyPDF2 is synchronous, so we run it in a thread
            def _read_pdf(content):
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                return "\n".join(text_parts)
            
            text_content = [await asyncio.to_thread(_read_pdf, file_content)]
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        raise
    
    return "\n\n".join(text_content)


async def parse_docx(file_path: str) -> str:
    """
    Parse a Word document (.docx) and extract text content.
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        Extracted text content
    """
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx not available. Please install python-docx.")
    
    try:
        # python-docx is synchronous, so we run it in a thread
        def _read_docx(path):
            doc = Document(path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(paragraphs)
        
        text_content = await asyncio.to_thread(_read_docx, file_path)
        return text_content
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}")
        raise


async def parse_txt(file_path: str) -> str:
    """
    Parse a text file and extract content.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        File content as string
    """
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return content
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                content = await f.read()
            return content
        except Exception as e:
            logger.error(f"Error parsing TXT {file_path}: {e}")
            raise
    except Exception as e:
        logger.error(f"Error parsing TXT {file_path}: {e}")
        raise


async def parse_json(file_path: str) -> str:
    """
    Parse a JSON file and convert it to readable text format.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        JSON content formatted as readable text
    """
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Parse JSON and format as readable text
        data = json.loads(content)
        
        # Convert JSON to a readable text format
        def format_json_value(key, value, indent=0):
            """Recursively format JSON into readable text."""
            indent_str = "  " * indent
            if isinstance(value, dict):
                lines = [f"{indent_str}{key}:"]
                for k, v in value.items():
                    lines.append(format_json_value(k, v, indent + 1))
                return "\n".join(lines)
            elif isinstance(value, list):
                lines = [f"{indent_str}{key}:"]
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        lines.append(f"{indent_str}  Item {i + 1}:")
                        for k, v in item.items():
                            lines.append(format_json_value(k, v, indent + 2))
                    else:
                        lines.append(f"{indent_str}  - {item}")
                return "\n".join(lines)
            else:
                return f"{indent_str}{key}: {value}"
        
        if isinstance(data, dict):
            text_parts = []
            for key, value in data.items():
                text_parts.append(format_json_value(key, value))
            return "\n\n".join(text_parts)
        else:
            return json.dumps(data, indent=2)
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error parsing JSON {file_path}: {e}")
        raise


async def parse_csv(file_path: str) -> str:
    """
    Parse a CSV file and convert it to readable text format.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        CSV content formatted as readable text
    """
    try:
        import csv
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Parse CSV
        lines = []
        reader = csv.reader(content.splitlines())
        headers = next(reader, None)
        
        if headers:
            lines.append(" | ".join(headers))
            lines.append("-" * len(" | ".join(headers)))
            
            for row in reader:
                lines.append(" | ".join(row))
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error parsing CSV {file_path}: {e}")
        raise


async def parse_document(file_path: str, file_type: str, filename: str) -> Dict[str, Any]:
    """
    Parse a single document based on its file type.
    
    Args:
        file_path: Path to the file
        file_type: MIME type of the file
        filename: Original filename
        
    Returns:
        Dictionary with 'filename', 'content', and 'file_type'
    """
    try:
        # Determine parser based on file type or extension
        file_ext = Path(filename).suffix.lower()
        
        if file_type == "application/pdf" or file_ext == ".pdf":
            content = await parse_pdf(file_path)
        elif file_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ] or file_ext in [".doc", ".docx"]:
            content = await parse_docx(file_path)
        elif file_type == "text/plain" or file_ext == ".txt":
            content = await parse_txt(file_path)
        elif file_type == "application/json" or file_ext == ".json":
            content = await parse_json(file_path)
        elif file_type == "text/csv" or file_ext == ".csv":
            content = await parse_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return {
            "filename": filename,
            "file_path": file_path,
            "content": content,
            "file_type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error parsing document {file_path}: {e}")
        raise


async def parse_documents_parallel(
    file_paths: List[str],
    file_types: List[str],
    filenames: List[str],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Parse multiple documents in parallel.
    
    Args:
        file_paths: List of file paths to parse
        file_types: List of MIME types corresponding to file_paths
        filenames: List of original filenames
        max_concurrent: Maximum number of documents to parse concurrently
        
    Returns:
        List of parsed document dictionaries
    """
    if len(file_paths) != len(file_types) or len(file_paths) != len(filenames):
        raise ValueError("file_paths, file_types, and filenames must have the same length")
    
    logger.info(f"Starting parallel parsing of {len(file_paths)} documents")
    
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def parse_with_semaphore(file_path, file_type, filename):
        async with semaphore:
            try:
                return await parse_document(file_path, file_type, filename)
            except Exception as e:
                logger.error(f"Failed to parse {filename}: {e}")
                return None
    
    # Create tasks for all documents
    tasks = [
        parse_with_semaphore(file_path, file_type, filename)
        for file_path, file_type, filename in zip(file_paths, file_types, filenames)
    ]
    
    # Execute all tasks in parallel
    parsed_docs = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    for doc in parsed_docs:
        if doc and not isinstance(doc, Exception):
            results.append(doc)
        elif isinstance(doc, Exception):
            logger.error(f"Exception during parsing: {doc}")
    
    logger.info(f"Successfully parsed {len(results)} out of {len(file_paths)} documents")
    return results


class DocumentParser:
    """Document parser for processing uploaded files."""
    
    def __init__(self, chunk_size: int = 1000, max_concurrent: int = 5):
        self.chunk_size = chunk_size
        self.max_concurrent = max_concurrent
    
    async def parse_files(
        self,
        file_paths: List[str],
        file_types: List[str],
        filenames: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Parse multiple files and return processed content.
        
        Args:
            file_paths: List of file paths to parse
            file_types: List of MIME types
            filenames: List of original filenames
            
        Returns:
            List of dictionaries with processed content ready for ChromaDB
        """
        if not file_paths:
            return []
        
        # Parse documents in parallel
        parsed_docs = await parse_documents_parallel(
            file_paths, file_types, filenames, max_concurrent=self.max_concurrent
        )
        
        # Convert to format similar to scraper results
        results = []
        for doc in parsed_docs:
            results.append({
                'url': f"file://{doc['file_path']}",
                'markdown': doc['content'],
                'filename': doc['filename'],
                'file_type': doc['file_type']
            })
        
        logger.info(f"Document parsing completed. Found {len(results)} documents")
        return results
    
    def process_content_for_chromadb(self, parse_results: List[Dict[str, Any]]) -> tuple:
        """
        Process parsed content into format suitable for ChromaDB.
        Uses the same chunking strategy as WebsiteScraper.
        
        Args:
            parse_results: Results from parse_files
            
        Returns:
            Tuple of (ids, documents, metadatas)
        """
        from .scraper import smart_chunk_markdown, extract_section_info
        
        ids, documents, metadatas = [], [], []
        chunk_idx = 0
        
        for doc in parse_results:
            source = doc.get('url', doc.get('filename', 'unknown'))
            filename = doc.get('filename', 'unknown')
            file_type = doc.get('file_type', 'unknown')
            content = doc['markdown']
            
            # Chunk the content using the same strategy as web scraping
            chunks = smart_chunk_markdown(content, max_len=self.chunk_size)
            
            for chunk in chunks:
                ids.append(f"file-chunk-{chunk_idx}")
                documents.append(chunk)
                
                # Create metadata
                meta = extract_section_info(chunk)
                meta["chunk_index"] = chunk_idx
                meta["source"] = source
                meta["filename"] = filename
                meta["file_type"] = file_type
                meta["document_type"] = "uploaded_file"
                metadatas.append(meta)
                
                chunk_idx += 1
        
        logger.info(f"Processed content into {len(documents)} chunks")
        return ids, documents, metadatas

