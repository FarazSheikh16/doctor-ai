from src.qdrant_handler import QdrantManager
from src.utils import setup_logger, load_config
from typing import List, Dict, Optional
import requests

class RAGModule:
    def __init__(self, config_path: str):
        """
        Initialize RAG module with configurations.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.qdrant_manager = QdrantManager(config_path)
        self.logger = setup_logger()
        self.llm_config = self.config['llm']
        self.search_config = self.config['search']
        
    def _format_context(self, search_results: List[Dict]) -> str:
        """Format search results into a context string."""
        context_parts = []
        for i, result in enumerate(search_results, 1):
            metadata = result['metadata']
            text = result['text']
            score = result['score']
            
            # Only include results above the score threshold
            if score >= self.search_config['score_threshold']:
                context_part = (
                    f"Source {i}:\n"
                    f"Title: {metadata.get('page_title', 'Unknown')}\n"
                    f"Section: {metadata.get('heading', 'N/A')}\n"
                    f"Content: {text}\n"
                )
                context_parts.append(context_part)
        
        return "\n\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create a specialized prompt for an oncology-focused AI assistant,
        emphasizing cancer-related medical expertise and patient communication.
        """
        system_prompt = self.llm_config['system_prompt']
        prompt = system_prompt.format(context=context, query=query)

        return prompt

    def _generate_response_with_ollama(self, prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            payload = {
                "model": self.llm_config['model_name'],
                "prompt": prompt,
                "stream": False,
                "temperature": self.llm_config['temperature'],
                "max_tokens": self.llm_config['max_tokens']
            }
            
            response = requests.post(
                self.llm_config['api_url'], 
                json=payload,
                timeout=900 # 30 seconds timeout
            )
            response.raise_for_status()
            
            return response.json()['response']
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Ollama API: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise

    def get_response(
        self, 
        query: str, 
        filter_conditions: Optional[Dict] = None, 
        num_results: Optional[int] = None
    ) -> Dict:
        """Get response using RAG approach."""
        try:
            # Use default limit from config if num_results not specified
            if num_results is None:
                num_results = self.search_config['default_limit']
                
            # Step 1: Search relevant documents
            self.logger.info(f"Searching for documents related to: {query}")
            search_results = self.qdrant_manager.search(
                text=query,
                filter_conditions=filter_conditions,
                limit=num_results
            )
            
            if not search_results:
                return {
                    'response': "I couldn't find any relevant information to answer your question.",
                    'sources': [],
                    'relevant_results': 0
                }
            
            # Step 2: Format context
            context = self._format_context(search_results)
            
            # Step 3: Create prompt
            prompt = self._create_prompt(query, context)
            
            # Step 4: Generate response
            self.logger.info("Generating response using LLM")
            response = self._generate_response_with_ollama(prompt)
            
            # Step 5: Prepare source information
            sources = [
                {
                    'title': result['metadata'].get('page_title', 'Unknown'),
                    'section': result['metadata'].get('heading', 'N/A'),
                    'score': result['score']
                }
                for result in search_results
                if result['score'] >= self.search_config['score_threshold']
            ]
            
            return {
                'response': response,
                'sources': sources,
                'relevant_results': len(sources)
            }
            
        except Exception as e:
            self.logger.error(f"Error in RAG pipeline: {e}")
            raise