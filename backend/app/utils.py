"""Utility functions for text processing and ChromaDB operations."""

import os
import pathlib
import asyncio
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions
from more_itertools import batched

logger = logging.getLogger(__name__)


def get_chroma_client(persist_directory: str) -> chromadb.PersistentClient:
    """Get a ChromaDB client with the specified persistence directory.

    Args:
        persist_directory: Directory where ChromaDB will store its data

    Returns:
        A ChromaDB PersistentClient
    """
    # Create the directory if it doesn't exist
    os.makedirs(persist_directory, exist_ok=True)

    # Return the client
    return chromadb.PersistentClient(persist_directory)


def collection_exists(client: chromadb.PersistentClient, collection_name: str) -> bool:
    """Check if a collection exists without initializing the embedding function.
    
    This is a lightweight check that doesn't trigger model downloads.
    
    Args:
        client: ChromaDB client
        collection_name: Name of the collection to check
        
    Returns:
        True if collection exists, False otherwise
    """
    try:
        collections = client.list_collections()
        return any(col.name == collection_name for col in collections)
    except Exception:
        return False


def get_or_create_collection(
        client: chromadb.PersistentClient,
        collection_name: str,
        embedding_model_name: str = None,  # Use ChromaDB default embedding function
        distance_function: str = "cosine",
) -> chromadb.Collection:
    """Get an existing collection or create a new one if it doesn't exist.

    Args:
        client: ChromaDB client
        collection_name: Name of the collection
        embedding_model_name: Name of the embedding model to use (deprecated, kept for compatibility)
        distance_function: Distance function to use for similarity search

    Returns:
        A ChromaDB Collection
    """
    # Use ChromaDB's default embedding function (no external API calls to Hugging Face)
    # DefaultEmbeddingFunction uses a local model and doesn't require external API access
    embedding_func = embedding_functions.DefaultEmbeddingFunction()

    # Try to get the collection, create it if it doesn't exist
    try:
        return client.get_collection(
            name=collection_name,
            embedding_function=embedding_func
        )
    except Exception:
        return client.create_collection(
            name=collection_name,
            embedding_function=embedding_func,
            metadata={"hnsw:space": distance_function}
        )


async def add_documents_to_collection(
        collection: chromadb.Collection,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100,
) -> None:
    """Add documents to a ChromaDB collection in batches asynchronously.
    
    This function is non-blocking and yields control to the event loop between batches
    to prevent UI/backend unresponsiveness.

    Args:
        collection: ChromaDB collection
        ids: List of document IDs
        documents: List of document texts
        metadatas: Optional list of metadata dictionaries for each document
        batch_size: Size of batches for adding documents
    """
    # Create default metadata if none provided
    if metadatas is None:
        metadatas = [{}] * len(documents)

    # Create document indices
    document_indices = list(range(len(documents)))
    
    total_batches = (len(documents) + batch_size - 1) // batch_size
    logger.info(f"Adding {len(documents)} documents to collection in {total_batches} batches")

    # Add documents in batches
    for batch_num, batch in enumerate(batched(document_indices, batch_size), 1):
        # Get the start and end indices for the current batch
        start_idx = batch[0]
        end_idx = batch[-1] + 1  # +1 because end_idx is exclusive
        
        # Log progress
        if batch_num % 10 == 0 or batch_num == total_batches:
            logger.info(f"Processing batch {batch_num}/{total_batches} ({start_idx}-{end_idx-1} of {len(documents)})")

        # Run ChromaDB add operation in thread pool to avoid blocking
        def _add_batch():
            collection.add(
                ids=ids[start_idx:end_idx],
                documents=documents[start_idx:end_idx],
                metadatas=metadatas[start_idx:end_idx],
            )
        
        # Execute in thread pool to avoid blocking event loop
        await asyncio.to_thread(_add_batch)
        
        # Yield control to event loop between batches to keep UI/backend responsive
        # This allows other async operations to run while we're processing
        await asyncio.sleep(0)
    
    logger.info(f"Successfully added {len(documents)} documents to collection")


def query_collection(
        collection: chromadb.Collection,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Query a ChromaDB collection for similar documents.

    Args:
        collection: ChromaDB collection
        query_text: Text to search for
        n_results: Number of results to return
        where: Optional filter to apply to the query

    Returns:
        Query results containing documents, metadatas, distances, and ids
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 VECTOR SEARCH QUERY: '{query_text}'")
    logger.info(f"📊 Searching collection: '{collection.name}' with n_results: {n_results}")
    
    # Query the collection
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    # Log detailed results
    logger.info(f"🎯 VECTOR SEARCH RESULTS:")
    logger.info(f"   📈 Total documents found: {len(results.get('documents', [[]])[0])}")
    
    if results.get('documents') and results['documents'][0]:
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0]
        )):
            relevance_score = 1 - distance
            logger.info(f"   📄 Document {i+1}:")
            logger.info(f"      🎯 Relevance Score: {relevance_score:.3f} (distance: {distance:.3f})")
            logger.info(f"      📋 Metadata: {metadata}")
            logger.info(f"      📝 Content Preview: {doc[:200]}{'...' if len(doc) > 200 else ''}")
            logger.info(f"      📏 Content Length: {len(doc)} characters")
    else:
        logger.warning("   ⚠️  No documents found in vector search!")
    
    return results


def format_results_as_context(query_results: Dict[str, Any]) -> str:
    """Format query results as a context string for the agent.

    Args:
        query_results: Results from a ChromaDB query

    Returns:
        Formatted context string
    """
    context = "CONTEXT INFORMATION:\n\n"

    for i, (doc, metadata, distance) in enumerate(zip(
            query_results["documents"][0],
            query_results["metadatas"][0],
            query_results["distances"][0]
    )):
        # Get title from metadata, fallback to source URL or generic label
        title = metadata.get('title', metadata.get('source', f'Document {i + 1}'))
        source_url = metadata.get('source', '')

        # Add document information with title
        context += f"Source: {title}\n"
        if source_url and source_url != title:
            context += f"URL: {source_url}\n"
        context += f"Relevance: {1 - distance:.2f}\n"

        # Add document content
        context += f"Content: {doc}\n\n"

    return context
