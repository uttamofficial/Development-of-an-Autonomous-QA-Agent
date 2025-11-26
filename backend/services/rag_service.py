"""
Service for RAG-based test case generation.
"""
import json
from typing import List
from uuid import uuid4

from backend.core.config import get_settings
from backend.core.vector_store import VectorStore
from backend.core.llm_client import DummyLLMClient
from backend.models.test_case import TestCase


class RAGService:
    """Handles RAG operations for test case generation."""
    
    def __init__(self):
        """Initialize the RAG service."""
        self.settings = get_settings()
        
        # Initialize vector store
        self.vector_store = VectorStore(
            db_path=self.settings.vector_db_path,
            collection_name=self.settings.chroma_collection_name,
            embedding_model_name=self.settings.embedding_model_name
        )
        
        # Initialize dummy LLM client (no API key needed)
        self.llm_client = DummyLLMClient(
            api_key="",  # Not used for dummy client
            model="dummy-local"
        )
    
    def generate_test_cases(self, query: str) -> List[TestCase]:
        """
        Generate test cases using RAG.
        
        Args:
            query: User query for test case generation
            
        Returns:
            List of TestCase objects
        """
        # Step 1: Query vector store for relevant chunks
        relevant_chunks = self.vector_store.query(query, top_k=10)
        
        if not relevant_chunks:
            raise ValueError(
                "No relevant documents found in knowledge base. "
                "Please upload documents and build the knowledge base first."
            )
        
        # Step 2: Construct prompt with context
        context_text = self._build_context_text(relevant_chunks)
        
        # Extract source documents for grounding
        source_docs = []
        for chunk in relevant_chunks:
            source = chunk.get('metadata', {}).get('source_document', '')
            if source and source not in source_docs:
                source_docs.append(source)
        
        system_prompt = f"""You are a QA test case generation expert. Your task is to generate test cases based ONLY on the provided context documents. You must NOT invent or hallucinate any features, requirements, or behaviors that are not explicitly mentioned in the context.

CRITICAL RULES:
1. ONLY use information from the provided context documents
2. Do NOT add any features, requirements, or behaviors not in the context
3. Each test case must reference the source documents it is based on in the 'grounded_in' field
4. Output a valid JSON array of test cases matching the exact schema provided
5. If the context doesn't contain enough information to generate meaningful test cases, generate fewer test cases or indicate limitations

Source documents available: {', '.join(source_docs[:5])}

Test Case Schema:
{{
  "test_id": "unique_id",
  "feature": "feature name",
  "test_scenario": "description of what is being tested",
  "preconditions": "required conditions before test (can be null)",
  "steps": ["step1", "step2", ...],
  "expected_result": "what should happen",
  "test_type": "positive|negative|boundary|edge_case",
  "grounded_in": ["source_document1", "source_document2", ...]
}}"""

        user_prompt = f"""Based on the following context documents, generate test cases for the following query:

QUERY: {query}

CONTEXT DOCUMENTS:
{context_text}

INSTRUCTIONS:
1. Analyze the context documents carefully
2. Generate test cases that are directly based on the information in the context
3. For each test case, include the source document names in the 'grounded_in' field (use the source_document values from the context)
4. Generate a variety of test types (positive, negative, boundary) when applicable
5. Ensure each test case has clear, actionable steps
6. Output ONLY a valid JSON array of test cases, no additional text or explanation

Return a JSON array of test cases following this exact format:
[
  {{
    "test_id": "TC001",
    "feature": "Feature Name",
    "test_scenario": "Scenario description",
    "preconditions": "Preconditions or null",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "expected_result": "Expected outcome",
    "test_type": "positive",
    "grounded_in": ["document1.md", "document2.txt"]
  }},
  ...
]"""

        # Step 3: Call dummy LLM
        try:
            response_text = self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
        except Exception as e:
            raise RuntimeError(f"Error generating test cases with LLM: {str(e)}")
        
        # Step 4: Parse JSON response
        test_cases = self._parse_llm_response(response_text, source_docs)
        
        return test_cases
    
    def _build_context_text(self, chunks: List[dict]) -> str:
        """
        Build formatted context text from retrieved chunks.
        
        Args:
            chunks: List of chunk dictionaries from vector store
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            source_doc = chunk.get('metadata', {}).get('source_document', 'Unknown')
            doc_type = chunk.get('metadata', {}).get('doc_type', 'unknown')
            text = chunk.get('text', '')
            
            context_parts.append(
                f"[Document {i}]\n"
                f"Source: {source_doc}\n"
                f"Type: {doc_type}\n"
                f"Content:\n{text}\n"
                f"---"
            )
        
        return "\n\n".join(context_parts)
    
    def _parse_llm_response(self, response_text: str, source_docs: List[str]) -> List[TestCase]:
        """
        Parse LLM JSON response into TestCase objects.
        
        Args:
            response_text: Raw response text from LLM
            source_docs: List of source documents for grounding
            
        Returns:
            List of TestCase objects
            
        Raises:
            ValueError: If response cannot be parsed
        """
        # Clean response text - remove markdown code blocks if present
        response_text = response_text.strip()
        
        # Remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            # Parse JSON
            data = json.loads(response_text)
            
            # Ensure it's a list
            if not isinstance(data, list):
                raise ValueError("LLM response is not a JSON array")
            
            # Parse each test case
            test_cases = []
            for item in data:
                try:
                    # Ensure grounded_in is a list and includes source docs
                    if 'grounded_in' not in item or not item['grounded_in']:
                        # Use source_docs from vector store if not provided
                        item['grounded_in'] = source_docs[:2] if source_docs else []
                    else:
                        # Ensure grounded_in references actual source documents
                        item['grounded_in'] = [doc for doc in item['grounded_in'] if doc in source_docs] or source_docs[:2]
                    
                    # Generate test_id if missing
                    if 'test_id' not in item or not item['test_id']:
                        item['test_id'] = f"TC_{uuid4().hex[:6].upper()}"
                    
                    test_case = TestCase(**item)
                    test_cases.append(test_case)
                except Exception as e:
                    # Skip invalid test cases but log the error
                    print(f"Warning: Skipping invalid test case: {str(e)}")
                    continue
            
            if not test_cases:
                raise ValueError("No valid test cases could be parsed from LLM response")
            
            return test_cases
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse LLM response as JSON: {str(e)}\n"
                f"Response text: {response_text[:500]}"
            )
