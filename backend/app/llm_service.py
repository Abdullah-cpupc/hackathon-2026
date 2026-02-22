"""
LLM Service for AI Chat Backend using Google Gemini API.
Based on the provided rag_bot.py implementation.
"""

import os
import logging
from typing import Optional
from google.genai import Client
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    """
    A singleton-like class to load and hold the Google Gemini model
    to prevent reloading it on every API request.
    """

    _instance = None
    _model_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._model_loaded:
            self.model = None
            self.client = None
            self.model_name = None
            self._load_model()
            ModelLoader._model_loaded = True

    def _load_model(self):
        """Loads the Google Gemini model using the new API pattern."""
        try:
            logger.info("Loading Google Gemini model...")
            
            # Configure the API key
            api_key = settings.google_api_key
            if not api_key:
                logger.error("GEMINI_API_KEY or GOOGLE_API_KEY not set in settings")
                self.model = self._create_mock_pipeline()
                return
            
            # Use new google.genai Client API (per quickstart guide)
            # The client can also get the API key from GEMINI_API_KEY env var automatically
            self.client = Client(api_key=api_key)
            self.model_name = 'gemini-2.5-flash'  # Using stable model from quickstart guide
            
            logger.info(f"Google Gemini client initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load Google Gemini model: {e}")
            # Fallback to a mock pipeline
            self.model = self._create_mock_pipeline()
            self.client = None
            self.model_name = None

    def _create_mock_pipeline(self):
        """Create a mock pipeline for testing when Gemini is not available."""
        logger.warning("Using mock pipeline - Google Gemini model not available")
        
        class MockPipeline:
            def __init__(self):
                self.tokenizer = None
            
            def generate_content(self, prompt):
                # Mock response for testing
                class MockResponse:
                    def __init__(self):
                        self.text = "This is a mock AI response. The actual Google Gemini model is not available in this environment."
                return MockResponse()
        
        return MockPipeline()
    
    def generate_content(self, contents: str) -> str:
        """
        Generate content using the new Gemini API pattern.
        This method wraps the new API to maintain compatibility with existing code.
        """
        if not self.client or not self.model_name:
            # Fallback to mock if client not initialized
            mock = self._create_mock_pipeline()
            return mock.generate_content(contents).text
        
        try:
            # Use the new API pattern from quickstart guide
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {e}")
            raise

    def get_model(self):
        """Get the model loader instance (for backward compatibility)."""
        return self
    
    def get_client(self):
        """Get the Gemini client."""
        return self.client


class RAG_Bot_Local:
    """
    A modular RAG bot designed for an API environment.
    It uses a pre-loaded Google Gemini model for efficient inference.
    """

    def __init__(self, collection_name: str, gemini_model, db_directory: str = "./chroma_db",
                 embedding_model: str = None):
        """
        Initializes the RAG_Bot_Local for a specific request.

        Args:
            collection_name (str): The name of the ChromaDB collection (derived from unique_id).
            gemini_model: The pre-loaded Google Gemini model from ModelLoader.
            db_directory (str, optional): The directory for ChromaDB. Defaults to "./chroma_db".
            embedding_model (str, optional): The embedding model name (deprecated, kept for compatibility). 
                                            Uses ChromaDB default embedding function to avoid external API calls.
        """
        from .utils import get_chroma_client, get_or_create_collection
        
        # --- 1. Connect to the specific ChromaDB collection ---
        self.client = get_chroma_client(db_directory)
        self.collection = get_or_create_collection(
            self.client,
            collection_name,
            embedding_model_name=embedding_model
        )

        # --- 2. Use the pre-loaded Gemini model ---
        self.gemini_model = gemini_model

        # --- 3. Define the system prompt ---
        self.system_prompt = (
            "You are a helpful AI assistant for this website. "
            "Answer questions using the retrieved context provided. "

            "IMPORTANT - Keep responses focused and minimal: "
            "- Only include information directly relevant to what was asked "
            "- Do not include tangential details (timezone, email, location) unless specifically asked "
            "- Summarize lists briefly instead of exhaustively listing every item "
            "- Prefer 2-3 sentences over paragraphs when possible "

            "If the question is unrelated to the website content, say: "
            "\"I can only help with questions about this website.\" "

            "End with a brief Sources section using page titles and URLs from the context. "
            "Never use generic labels like 'Document 1'. Format as: Title (URL) "

            "Do not repeat the question or mention internal workings."
        )



    def _generate_response(self, prompt: str) -> str:
        """Generates a response using the Google Gemini model."""

        try:
            # Create the full prompt with system instructions
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            
            logger.info(f"🔧 SYSTEM PROMPT: {self.system_prompt}")
            logger.info(f"📝 FULL PROMPT TO GEMINI (length: {len(full_prompt)} chars):")
            logger.info(f"   {full_prompt[:400]}{'...' if len(full_prompt) > 400 else ''}")
            
            # Generate content using Gemini
            # The gemini_model is a ModelLoader instance with generate_content method
            if hasattr(self.gemini_model, 'generate_content'):
                # New API pattern - ModelLoader.generate_content returns string directly
                response_text = self.gemini_model.generate_content(full_prompt)
            elif hasattr(self.gemini_model, 'generate_content') and callable(getattr(self.gemini_model, 'generate_content', None)):
                # Try calling it and check if it returns a response object
                response = self.gemini_model.generate_content(full_prompt)
                response_text = response.text if hasattr(response, 'text') else str(response)
            else:
                # Fallback for mock pipeline
                response = self.gemini_model.generate_content(full_prompt)
                response_text = response.text if hasattr(response, 'text') else str(response)
            
            logger.info(f"🤖 GEMINI RAW RESPONSE:")
            logger.info(f"   📏 Response length: {len(response_text)} characters")
            logger.info(f"   📄 Raw response: {response_text}")
            
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"

    def answer(self, query: str, n_results: int = 5) -> str:
        """Answers a user's query using the RAG pipeline."""
        try:
            from .utils import query_collection, format_results_as_context
            
            logger.info(f"🤖 AI QUERY RECEIVED: '{query}'")
            logger.info(f"🔧 Collection: '{self.collection.name}', n_results: {n_results}")
            
            # 1. Retrieve context
            query_results = query_collection(self.collection, query, n_results=n_results)
            
            # Check if we have any results
            if not query_results["documents"] or not query_results["documents"][0]:
                logger.warning("❌ No documents found in vector search - returning fallback response")
                return "I don't have any information about this topic in my knowledge base. Please try asking about something else related to the website content."
            
            context_string = format_results_as_context(query_results)
            logger.info(f"📝 FORMATTED CONTEXT SENT TO AI:")
            logger.info(f"   📏 Context length: {len(context_string)} characters")
            logger.info(f"   📄 Context preview: {context_string[:500]}{'...' if len(context_string) > 500 else ''}")

            # 2. Construct the prompt
            prompt_template = (
                "Here is the context retrieved from the website's documents:\n\n"
                "--- CONTEXT ---\n"
                "{context}\n"
                "--- END CONTEXT ---\n\n"
                "Based on the context above, please answer the following question:\n"
                "Question: {question}"
            )
            final_prompt = prompt_template.format(context=context_string, question=query)
            
            logger.info(f"🎯 FINAL PROMPT TO GEMINI:")
            logger.info(f"   📏 Prompt length: {len(final_prompt)} characters")
            logger.info(f"   📄 Prompt preview: {final_prompt[:300]}{'...' if len(final_prompt) > 300 else ''}")

            # 3. Generate and return response
            logger.info("🚀 Sending request to Gemini model...")
            response = self._generate_response(final_prompt)
            logger.info(f"✅ GEMINI RESPONSE RECEIVED:")
            logger.info(f"   📏 Response length: {len(response)} characters")
            logger.info(f"   📄 Response: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in RAG answer generation: {e}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"

    def get_collection_info(self) -> dict:
        """Get information about the current collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection.name,
                "document_count": count,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "collection_name": self.collection.name,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }
