from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import PromptTemplate
from src.qdrant_handler import QdrantManager
from src.utils import setup_logger, load_config
from typing import List, Dict, Optional

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
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize the chains
        self._initialize_chains()

    @property
    def llm(self) -> LlamaCpp:
        """
        Property to access or create LLM instance using singleton pattern.
        Returns:
            LlamaCpp: Instance of the LLM
        """
        if not self.__class__._llm_instance:
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            self.__class__._llm_instance = LlamaCpp(
                model_path=self.llm_config['model_path'],
                temperature=self.llm_config.get('temperature', 0.7),
                n_ctx=self.llm_config.get('n_ctx', 2048),
                max_tokens=self.llm_config.get('max_tokens', 512),
                callback_manager=callback_manager,
                verbose=True
            )
        
        return self.__class__._llm_instance

    def _initialize_chains(self):
        """Initialize the LLMChains for query refinement and response generation."""
        # Create refinement prompt template
        refinement_prompt = PromptTemplate(
            template=self.llm_config['refinement_prompt'],
            input_variables=["context", "query"]
        )
        
        # Create response prompt template
        response_prompt = PromptTemplate(
            template=self.llm_config['system_prompt'],
            input_variables=["context", "query"]
        )

        # Initialize the chains
        self.refinement_chain = LLMChain(
            llm=self.llm,
            prompt=refinement_prompt,
            verbose=True
        )
        
        self.response_chain = LLMChain(
            llm=self.llm,
            prompt=response_prompt,
            verbose=True
        )

    def _refine_query(self, query: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Generate a standalone question based on the new query and conversation history.
        If generation fails, return the original query.
        """
        try:
            # If no history, return original query
            if not conversation_history or len(conversation_history) < 2:
                return query


            # Create history text from the last three entries in the conversation
            history_text = "\n".join([
                f"{entry['role']}: {entry['message']}" 
                for entry in conversation_history
            ])
            
            # Use LangChain's LLMChain to generate the standalone question
            result = self.refinement_chain.run(
                context=history_text,
                query=query
            )
            
            # Since the updated prompt outputs only the standalone question,
            # directly return the result after stripping extra whitespace
            refined_query = result.strip()
            self.logger.info(f"Generated standalone question: '{refined_query}'")
            return refined_query
            
        except Exception as e:
            self.logger.error(f"Error in query refinement: {e}")
            return query


    def _format_context(self, search_results: List[Dict]) -> str:
        """Format search results into a context string."""
        context_parts = []
        for i, result in enumerate(search_results, 1):
            metadata = result['metadata']
            text = result['text']
            score = result['score']
            
            if score >= self.search_config['score_threshold']:
                context_part = (
                    f"Source {i}:\n"
                    f"Title: {metadata.get('page_title', 'Unknown')}\n"
                    f"Section: {metadata.get('heading', 'N/A')}\n"
                    f"Content: {text}\n"
                )
                context_parts.append(context_part)
        
        return "\n\n".join(context_parts)

    def get_response(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict]] = None, 
        filter_conditions: Optional[Dict] = None, 
        num_results: Optional[int] = None
    ) -> Dict:
        """Get response using RAG approach with conversation history."""
        try:
            # Step 1: Ensure conversation history is valid
            conversation_history = conversation_history or []

            # Step 2: Refine the query using only past history
            refined_query = self._refine_query(query, conversation_history)
            self.logger.info(f"Refined query: {refined_query}")

            # Step 3: Use default limit from config if num_results not specified
            if num_results is None:
                num_results = self.search_config['default_limit']
            
            # Step 4: Search for relevant documents with refined query
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

            # Step 5: Format context with search results
            context = self._format_context(search_results)

            # Step 6: Add conversation history if available
            if conversation_history:
                conversation_context = "\n".join([
                    f"{entry['role'].capitalize()}: {entry['message']}" 
                    for entry in conversation_history
                ])
                context = conversation_context + "\n\n" + context
            
            # Step 7: Generate response using LangChain's LLMChain
            response = self.response_chain.run(
                context=context,
                query=refined_query
            )
            
            # Step 8: Prepare source information
            sources = [
                {
                    'title': result['metadata'].get('page_title', 'Unknown'),
                    'section': result['metadata'].get('heading', 'N/A'),
                    'score': result['score']
                }
                for result in search_results
                if result['score'] >= self.search_config['score_threshold']
            ]

            # Step 9: Return the response and sources
            return {
                'response': response,
                'sources': sources,
                'relevant_results': len(sources)
            }
            
        except Exception as e:
            self.logger.error(f"Error in RAG pipeline: {e}")
            raise


    def clear_memory(self):
        """Clear the conversation memory."""
        self.memory.clear()