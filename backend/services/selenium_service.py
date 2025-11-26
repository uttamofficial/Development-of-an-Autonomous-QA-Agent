"""
Service for generating Selenium test scripts.
"""
import os
import json
from pathlib import Path
from typing import Dict, List

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from backend.core.config import get_settings
from backend.core.vector_store import VectorStore
from backend.core.llm_client import DummyLLMClient
from backend.models.test_case import TestCase


class SeleniumService:
    """Handles Selenium script generation."""
    
    def __init__(self):
        """Initialize the Selenium service."""
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
    
    def generate_selenium_script(self, test_case: TestCase) -> str:
        """
        Generate a Selenium Python script for a test case.
        
        Args:
            test_case: TestCase object
            
        Returns:
            Python Selenium script as string
            
        Raises:
            FileNotFoundError: If checkout.html is not found
            ValueError: If HTML cannot be parsed or script generation fails
        """
        # Step 1: Load checkout.html
        html_path = Path(self.settings.html_path) / "checkout.html"
        
        if not html_path.exists():
            raise FileNotFoundError(
                f"checkout.html not found at {html_path}. "
                "Please upload checkout.html first."
            )
        
        # Step 2: Parse checkout.html with BeautifulSoup
        html_structure = self._parse_html_structure(str(html_path))
        
        # Step 3: Get relevant documentation chunks from vector store
        # Query based on test case feature and grounded_in documents
        relevant_docs = self._get_relevant_documentation(test_case)
        
        # Step 4: Build prompt and generate script
        script = self._generate_script_with_llm(
            test_case=test_case,
            html_structure=html_structure,
            html_content=self._get_html_content(str(html_path)),
            relevant_docs=relevant_docs
        )
        
        return script
    
    def _parse_html_structure(self, html_path: str) -> Dict:
        """
        Parse checkout.html to identify form elements and selectors.
        
        Args:
            html_path: Path to checkout.html
            
        Returns:
            Dictionary with identified elements and their selectors
        """
        if BeautifulSoup is None:
            raise ImportError(
                "BeautifulSoup4 is required. Install it with: pip install beautifulsoup4"
            )
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        structure = {
            "form_fields": [],
            "discount_code_input": None,
            "shipping_methods": [],
            "payment_methods": [],
            "pay_now_button": None,
            "all_inputs": [],
            "all_buttons": [],
            "all_selects": []
        }
        
        # Find all form inputs
        inputs = soup.find_all('input')
        for inp in inputs:
            input_type = inp.get('type', '').lower()
            input_id = inp.get('id', '')
            input_name = inp.get('name', '')
            input_class = inp.get('class', [])
            
            input_info = {
                "type": input_type,
                "id": input_id,
                "name": input_name,
                "class": ' '.join(input_class) if input_class else '',
                "selector_id": f"#{input_id}" if input_id else None,
                "selector_name": f"[name='{input_name}']" if input_name else None,
                "selector_css": self._build_css_selector(inp)
            }
            
            structure["all_inputs"].append(input_info)
            
            # Categorize inputs
            if input_type in ['text', 'email', 'tel']:
                structure["form_fields"].append(input_info)
            elif input_type == 'text' and ('discount' in input_name.lower() or 'coupon' in input_name.lower() or 'code' in input_name.lower()):
                structure["discount_code_input"] = input_info
            elif input_type == 'radio':
                if 'shipping' in input_name.lower() or 'delivery' in input_name.lower():
                    structure["shipping_methods"].append(input_info)
                elif 'payment' in input_name.lower() or 'pay' in input_name.lower():
                    structure["payment_methods"].append(input_info)
        
        # Find discount code input (if not found above, look for specific patterns)
        if not structure["discount_code_input"]:
            discount_input = soup.find('input', {'name': lambda x: x and ('discount' in x.lower() or 'coupon' in x.lower() or 'promo' in x.lower())})
            if discount_input:
                structure["discount_code_input"] = {
                    "type": discount_input.get('type', ''),
                    "id": discount_input.get('id', ''),
                    "name": discount_input.get('name', ''),
                    "class": ' '.join(discount_input.get('class', [])),
                    "selector_id": f"#{discount_input.get('id')}" if discount_input.get('id') else None,
                    "selector_name": f"[name='{discount_input.get('name')}']" if discount_input.get('name') else None,
                    "selector_css": self._build_css_selector(discount_input)
                }
        
        # Find all buttons
        buttons = soup.find_all(['button', 'input'], {'type': lambda x: x and x.lower() in ['button', 'submit']})
        for btn in buttons:
            btn_id = btn.get('id', '')
            btn_name = btn.get('name', '')
            btn_text = btn.get_text(strip=True) if hasattr(btn, 'get_text') else btn.get('value', '')
            btn_class = btn.get('class', [])
            
            button_info = {
                "id": btn_id,
                "name": btn_name,
                "text": btn_text,
                "class": ' '.join(btn_class) if btn_class else '',
                "selector_id": f"#{btn_id}" if btn_id else None,
                "selector_name": f"[name='{btn_name}']" if btn_name else None,
                "selector_css": self._build_css_selector(btn)
            }
            
            structure["all_buttons"].append(button_info)
            
            # Check if it's the pay/submit button
            if 'pay' in btn_text.lower() or 'submit' in btn_text.lower() or 'checkout' in btn_text.lower() or 'place' in btn_text.lower():
                structure["pay_now_button"] = button_info
        
        # Find select elements
        selects = soup.find_all('select')
        for sel in selects:
            sel_id = sel.get('id', '')
            sel_name = sel.get('name', '')
            sel_class = sel.get('class', [])
            
            select_info = {
                "id": sel_id,
                "name": sel_name,
                "class": ' '.join(sel_class) if sel_class else '',
                "selector_id": f"#{sel_id}" if sel_id else None,
                "selector_name": f"[name='{sel_name}']" if sel_name else None,
                "selector_css": self._build_css_selector(sel)
            }
            
            structure["all_selects"].append(select_info)
        
        return structure
    
    def _build_css_selector(self, element) -> str:
        """
        Build a CSS selector for an element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            CSS selector string
        """
        # Prefer ID
        if element.get('id'):
            return f"#{element.get('id')}"
        
        # Then name
        if element.get('name'):
            return f"[name='{element.get('name')}']"
        
        # Then class
        classes = element.get('class', [])
        if classes:
            return f".{'.'.join(classes)}"
        
        # Fallback to tag
        return element.name
    
    def _get_html_content(self, html_path: str) -> str:
        """
        Get HTML content as string.
        
        Args:
            html_path: Path to HTML file
            
        Returns:
            HTML content
        """
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_relevant_documentation(self, test_case: TestCase) -> List[Dict]:
        """
        Get relevant documentation chunks from vector store based on test case.
        
        Args:
            test_case: TestCase object
            
        Returns:
            List of relevant document chunks
        """
        # Query based on feature and grounded_in documents
        query = f"{test_case.feature} {test_case.test_scenario}"
        
        # Get chunks from vector store
        chunks = self.vector_store.query(query, top_k=5)
        
        # Filter to prioritize documents mentioned in grounded_in
        if test_case.grounded_in:
            prioritized = []
            others = []
            
            for chunk in chunks:
                source = chunk.get('metadata', {}).get('source_document', '')
                if any(doc in source for doc in test_case.grounded_in):
                    prioritized.append(chunk)
                else:
                    others.append(chunk)
            
            return prioritized + others
        
        return chunks
    
    def _generate_script_with_llm(
        self,
        test_case: TestCase,
        html_structure: Dict,
        html_content: str,
        relevant_docs: List[Dict]
    ) -> str:
        """
        Generate Selenium script using dummy LLM.
        
        Args:
            test_case: TestCase object
            html_structure: Parsed HTML structure
            html_content: Full HTML content
            relevant_docs: Relevant documentation chunks
            
        Returns:
            Python Selenium script
        """
        # Build context from relevant docs
        doc_context = ""
        if relevant_docs:
            doc_parts = []
            for doc in relevant_docs[:3]:  # Limit to top 3
                source = doc.get('metadata', {}).get('source_document', 'Unknown')
                text = doc.get('text', '')
                doc_parts.append(f"[Source: {source}]\n{text}")
            doc_context = "\n\n---\n\n".join(doc_parts)
        
        system_prompt = """You are a Python Selenium automation expert. Your task is to generate clean, fully executable Selenium test scripts based on test cases and the provided HTML structure.

CRITICAL RULES:
1. Use ONLY the selectors that actually exist in the provided HTML structure
2. Do NOT invent HTML IDs, names, or CSS selectors that are not in the HTML
3. Prefer using IDs, then names, then CSS selectors in that order
4. Generate complete, runnable Python code
5. Include proper imports, setup, teardown, and assertions
6. Use explicit waits (WebDriverWait) instead of hard-coded sleeps
7. Make the code clean, well-commented, and maintainable"""

        # Build HTML structure summary
        html_summary = json.dumps(html_structure, indent=2)
        
        # Build test case JSON
        test_case_json = test_case.model_dump_json(indent=2)
        
        user_prompt = f"""Generate a complete Python Selenium test script for the following test case.

TEST CASE:
{test_case_json}

HTML STRUCTURE (identified elements and selectors):
{html_summary}

FULL HTML CONTENT:
```html
{html_content[:5000]}  # Limit to first 5000 chars to avoid token limits
```

RELEVANT DOCUMENTATION:
{doc_context if doc_context else "No additional documentation provided."}

INSTRUCTIONS:
1. Create a complete Python script using Selenium WebDriver
2. Use Chrome WebDriver (from selenium.webdriver.chrome.service import Service, from selenium.webdriver.chrome.options import Options)
3. Navigate to the checkout page (use a placeholder URL or file:// path)
4. Implement all test steps from the test case
5. Use ONLY the selectors provided in the HTML structure - do not invent any
6. Include proper waits using WebDriverWait and expected_conditions
7. Add assertions to verify expected results
8. Include proper setup and teardown (use try/finally or pytest fixtures if appropriate)
9. Make the script executable and well-commented
10. Handle any preconditions mentioned in the test case

OUTPUT FORMAT:
Return ONLY the Python code, no markdown code blocks, no explanations. The code should be ready to run."""

        try:
            response = self.llm_client.generate_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for more deterministic code
            )
            
            # Clean up response (remove markdown code blocks if present)
            script = response.strip()
            if script.startswith("```python"):
                script = script[9:]
            elif script.startswith("```"):
                script = script[3:]
            
            if script.endswith("```"):
                script = script[:-3]
            
            return script.strip()
            
        except Exception as e:
            raise ValueError(f"Error generating Selenium script: {str(e)}")
