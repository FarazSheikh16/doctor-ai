from src.qdrant_handler import QdrantManager
from src.utils import setup_logger, load_config
from typing import List, Dict, Optional
from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class RAGModule:
    _llm_instance = None 
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

    @property
    def llm(self) -> LlamaCpp:
        """
        Property to access or create LLM instance using singleton pattern.
        Returns:
            LlamaCpp: Instance of the LLM
        """
        if not self.__class__._llm_instance:
            # Initialize callback manager for LlamaCpp
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            # Initialize LlamaCpp model
            self.__class__._llm_instance = LlamaCpp(
                model_path=self.llm_config['model_path'],
                temperature=self.llm_config.get('temperature'),
                n_ctx=self.llm_config.get('n_ctx'),
                max_tokens=self.llm_config.get('max_tokens'),
                callback_manager=callback_manager,
                verbose=True
            )
        
        return self.__class__._llm_instance


    def _refine_query(self, query: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Refine the query if it's vague, using conversation history for context.
        Returns original query if it's specific enough or refinement fails.
        """
        try:
            # If no history, return original query
            if not conversation_history:
                return query

            # Create refinement prompt
            history_text = "\n".join([
                f"{entry['role']}: {entry['message']}" 
                for entry in conversation_history[-3:]  # Use last 3 messages for context
            ])
            
            refinement_prompt = self.llm_config['refinement_prompt'].format(
                context=history_text,
                query=query
            )
            
            # Use LlamaCpp for refinement
            result = self.llm(refinement_prompt).strip()
            
            # Parse the response
            if result.startswith("REFINED:"):
                refined_query = result.replace("REFINED:", "").strip()
                self.logger.info(f"Query refined from '{query}' to '{refined_query}'")
                return refined_query
            elif result.startswith("UNCHANGED:"):
                self.logger.info("Query determined to be specific enough")
                return query
            else:
                self.logger.warning("Unexpected refinement format, using original query")
                return query
                
        except Exception as e:
            self.logger.error(f"Error in query refinement: {e}")
            return query  # Return original query if refinement fails

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

    def _generate_response_with_llama(self, prompt: str) -> str:
        """Generate response using cached LlamaCpp instance."""
        try:
            return self.llm(prompt)
        except Exception as e:
            self.logger.error(f"Error generating response with LlamaCpp: {e}")
            raise

    def get_response(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict]] = None, 
        filter_conditions: Optional[Dict] = None, 
        num_results: Optional[int] = None
    ) -> Dict:
        """Get response using RAG approach with conversation history."""
        try:
            # Step 1: Refine the query if needed
            refined_query = self._refine_query(query, conversation_history)
            
            # Use default limit from config if num_results not specified
            if num_results is None:
                num_results = self.search_config['default_limit']
            
            # Step 2: Search relevant documents with refined query
            self.logger.info(f"Searching for documents related to: {refined_query}")
            search_results = self.qdrant_manager.search(
                text=refined_query,
                filter_conditions=filter_conditions,
                limit=num_results
            )
            
            if not search_results:
                return {
                    'response': "I couldn't find any relevant information to answer your question.",
                    'sources': [],
                    'relevant_results': 0
                }

            # Step 3: Format context based on search results
            context = self._format_context(search_results)

            # Step 4: Add previous conversation history (if available) to the context
            if conversation_history:
                conversation_context = "\n".join([
                    f"{entry['role'].capitalize()}: {entry['message']}" 
                    for entry in conversation_history
                ])
                context = conversation_context + "\n\n" + context
            
            # Step 5: Create prompt
            prompt = self._create_prompt(refined_query, context)

            # Step 6: Generate response
            self.logger.info("Generating response using LlamaCpp")
            response = self._generate_response_with_llama(prompt)
            
            # Step 7: Prepare source information
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