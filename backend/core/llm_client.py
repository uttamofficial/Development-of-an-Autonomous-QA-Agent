"""
LLM client for interacting with language models.
Uses a dummy offline model for local testing.
"""
import json
import re
from typing import Optional
from uuid import uuid4


class DummyLLMClient:
    """Dummy offline LLM client that generates deterministic responses."""
    
    def __init__(self, api_key: str = "", model: str = "dummy-local", base_url: Optional[str] = None):
        """
        Initialize the dummy LLM client.
        
        Args:
            api_key: Not used (kept for compatibility)
            model: Model name (not used)
            base_url: Not used (kept for compatibility)
        """
        self.model = model
    
    def generate_completion(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Generate text completion using dummy logic.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (used for context)
            temperature: Not used (kept for compatibility)
            
        Returns:
            Generated text
        """
        prompt_lower = prompt.lower()
        
        # Test case generation
        if "test case" in prompt_lower or "test cases" in prompt_lower:
            return self._generate_test_cases(prompt, system_prompt)
        
        # Selenium script generation
        if "selenium" in prompt_lower or "webdriver" in prompt_lower or "python" in prompt_lower and "driver" in prompt_lower:
            return self._generate_selenium_script(prompt, system_prompt)
        
        # Generic response
        return "This is a dummy LLM response. The system is running in offline mode."
    
    def _generate_test_cases(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate test cases in JSON format."""
        # Extract source documents from context if available
        source_docs = []
        
        # Look in both system_prompt and prompt for source documents
        search_text = (system_prompt or "") + " " + (prompt or "")
        
        # Look for source document references in various formats
        doc_patterns = [
            r'source[:\s]+([^\s,]+\.(md|txt|json|pdf))',
            r'Source documents available: ([^\n]+)',
            r'source_document["\']?\s*:\s*["\']?([^"\',\s]+\.(md|txt|json|pdf))',
            r'\[Source: ([^\]]+\.(md|txt|json|pdf))\]',
        ]
        
        for pattern in doc_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                doc = match[0] if isinstance(match, tuple) else match
                if doc and doc not in source_docs:
                    source_docs.append(doc)
        
        # Also look for common document names in the text
        common_docs = ["product_specs.md", "ui_ux_guide.txt", "api_endpoints.json", "checkout.html"]
        for doc in common_docs:
            if doc.lower() in search_text.lower() and doc not in source_docs:
                source_docs.append(doc)
        
        # Default sources if none found
        if not source_docs:
            source_docs = ["product_specs.md", "ui_ux_guide.txt"]
        
        # Determine test types based on prompt
        test_cases = []
        
        # Check if prompt mentions discount codes
        if "discount" in prompt.lower() or "coupon" in prompt.lower() or "code" in prompt.lower():
            # Positive test case
            test_cases.append({
                "test_id": "TC001",
                "feature": "Discount Code",
                "test_scenario": "Apply valid discount code SAVE15 to verify 15% discount is applied correctly",
                "preconditions": "User has items in cart",
                "steps": [
                    "Navigate to checkout page",
                    "Enter valid discount code 'SAVE15' in discount code field",
                    "Click 'Apply Discount' button",
                    "Verify discount message appears",
                    "Verify total price is reduced by 15%"
                ],
                "expected_result": "Discount of 15% is applied successfully and total price is updated",
                "test_type": "positive",
                "grounded_in": source_docs[:2]
            })
            
            # Negative test case
            test_cases.append({
                "test_id": "TC002",
                "feature": "Discount Code",
                "test_scenario": "Apply invalid discount code to verify error message is displayed",
                "preconditions": "User has items in cart",
                "steps": [
                    "Navigate to checkout page",
                    "Enter invalid discount code 'INVALID123' in discount code field",
                    "Click 'Apply Discount' button",
                    "Verify error message 'Invalid discount code' is displayed in red"
                ],
                "expected_result": "Error message 'Invalid discount code' is displayed in red text",
                "test_type": "negative",
                "grounded_in": source_docs[:2]
            })
        
        # Check if prompt mentions form validation
        if "validation" in prompt.lower() or "form" in prompt.lower() or "email" in prompt.lower():
            test_cases.append({
                "test_id": "TC003",
                "feature": "Form Validation",
                "test_scenario": "Submit form with invalid email to verify validation error",
                "preconditions": "User is on checkout page",
                "steps": [
                    "Enter invalid email format 'invalid-email' in email field",
                    "Click outside the email field (trigger validation)",
                    "Verify red error message appears below email field",
                    "Verify error message text: 'Please enter a valid email address'"
                ],
                "expected_result": "Red error message is displayed below email field indicating invalid email format",
                "test_type": "negative",
                "grounded_in": source_docs[:2]
            })
        
        # Check if prompt mentions shipping
        if "shipping" in prompt.lower():
            test_cases.append({
                "test_id": "TC004",
                "feature": "Shipping Method",
                "test_scenario": "Select Express shipping and verify $10 shipping cost is added",
                "preconditions": "User has items in cart",
                "steps": [
                    "Navigate to checkout page",
                    "Select 'Express Shipping' radio button",
                    "Verify shipping cost of $10.00 is added to total",
                    "Verify total price includes shipping cost"
                ],
                "expected_result": "Express shipping cost of $10.00 is added to order total",
                "test_type": "positive",
                "grounded_in": source_docs[:2]
            })
        
        # Default test cases if no specific feature mentioned
        if not test_cases:
            test_cases = [
                {
                    "test_id": "TC001",
                    "feature": "Checkout Process",
                    "test_scenario": "Complete checkout with valid information",
                    "preconditions": "User has items in cart",
                    "steps": [
                        "Fill in customer name field",
                        "Fill in valid email address",
                        "Fill in shipping address",
                        "Select shipping method",
                        "Select payment method",
                        "Click 'Pay Now' button"
                    ],
                    "expected_result": "Payment successful message is displayed",
                    "test_type": "positive",
                    "grounded_in": source_docs[:2]
                },
                {
                    "test_id": "TC002",
                    "feature": "Form Validation",
                    "test_scenario": "Submit form with missing required fields",
                    "preconditions": "User is on checkout page",
                    "steps": [
                        "Leave name field empty",
                        "Leave email field empty",
                        "Click 'Pay Now' button",
                        "Verify error messages appear for empty fields"
                    ],
                    "expected_result": "Red error messages are displayed for all empty required fields",
                    "test_type": "negative",
                    "grounded_in": source_docs[:2]
                }
            ]
        
        # Return as JSON string
        return json.dumps(test_cases, indent=2)
    
    def _generate_selenium_script(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate Selenium Python script."""
        # Extract selectors from prompt/HTML structure
        selectors = self._extract_selectors_from_prompt(prompt)
        
        # Extract test case info
        test_case_info = self._extract_test_case_info(prompt)
        
        # Build script
        script = f"""from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def test_checkout():
    \"\"\"
    Selenium test script for: {test_case_info.get('scenario', 'Checkout Test')}
    \"\"\"
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to checkout page
        # Update this URL to point to your checkout.html file
        driver.get("file:///path/to/checkout.html")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
"""
        
        # Add steps based on test case
        steps = test_case_info.get('steps', [])
        for i, step in enumerate(steps, 1):
            script += f"        # Step {i}: {step}\n"
            
            # Add Selenium code based on step content
            step_lower = step.lower()
            
            if "name" in step_lower or "customer name" in step_lower:
                selector = selectors.get('name', 'customer-name')
                script += f"        name_field = wait.until(EC.presence_of_element_located((By.ID, \"{selector}\")))\n"
                script += f"        name_field.clear()\n"
                script += f"        name_field.send_keys(\"John Doe\")\n\n"
            
            elif "email" in step_lower:
                selector = selectors.get('email', 'customer-email')
                script += f"        email_field = wait.until(EC.presence_of_element_located((By.ID, \"{selector}\")))\n"
                script += f"        email_field.clear()\n"
                script += f"        email_field.send_keys(\"john.doe@example.com\")\n\n"
            
            elif "address" in step_lower:
                selector = selectors.get('address', 'customer-address')
                script += f"        address_field = wait.until(EC.presence_of_element_located((By.ID, \"{selector}\")))\n"
                script += f"        address_field.clear()\n"
                script += f"        address_field.send_keys(\"123 Main St, City, State 12345\")\n\n"
            
            elif "discount" in step_lower or "coupon" in step_lower or "code" in step_lower:
                selector = selectors.get('discount', 'discount-code')
                if "invalid" in step_lower:
                    code_value = "INVALID123"
                else:
                    code_value = "SAVE15"
                script += f"        discount_field = wait.until(EC.presence_of_element_located((By.ID, \"{selector}\")))\n"
                script += f"        discount_field.clear()\n"
                script += f"        discount_field.send_keys(\"{code_value}\")\n\n"
                
                if "apply" in step_lower or "click" in step_lower:
                    script += f"        apply_button = driver.find_element(By.XPATH, \"//button[contains(text(), 'Apply')]\")\n"
                    script += f"        apply_button.click()\n"
                    script += f"        time.sleep(1)  # Wait for discount to apply\n\n"
            
            elif "shipping" in step_lower:
                if "express" in step_lower:
                    selector = selectors.get('shipping_express', 'shipping-express')
                    script += f"        express_shipping = wait.until(EC.element_to_be_clickable((By.ID, \"{selector}\")))\n"
                    script += f"        express_shipping.click()\n\n"
                else:
                    selector = selectors.get('shipping_standard', 'shipping-standard')
                    script += f"        standard_shipping = wait.until(EC.element_to_be_clickable((By.ID, \"{selector}\")))\n"
                    script += f"        standard_shipping.click()\n\n"
            
            elif "payment" in step_lower:
                if "paypal" in step_lower:
                    selector = selectors.get('payment_paypal', 'payment-paypal')
                    script += f"        paypal_payment = wait.until(EC.element_to_be_clickable((By.ID, \"{selector}\")))\n"
                    script += f"        paypal_payment.click()\n\n"
                else:
                    selector = selectors.get('payment_credit', 'payment-credit-card')
                    script += f"        credit_payment = wait.until(EC.element_to_be_clickable((By.ID, \"{selector}\")))\n"
                    script += f"        credit_payment.click()\n\n"
            
            elif "pay now" in step_lower or "submit" in step_lower or "click" in step_lower and "button" in step_lower:
                selector = selectors.get('pay_button', 'pay-now-button')
                script += f"        pay_button = wait.until(EC.element_to_be_clickable((By.ID, \"{selector}\")))\n"
                script += f"        pay_button.click()\n"
                script += f"        time.sleep(2)  # Wait for payment processing\n\n"
            
            elif "verify" in step_lower or "assert" in step_lower:
                if "error" in step_lower or "invalid" in step_lower:
                    script += f"        # Verify error message is displayed\n"
                    script += f"        error_message = driver.find_element(By.CLASS_NAME, \"error-message\")\n"
                    script += f"        assert error_message.is_displayed(), \"Error message should be visible\"\n"
                    script += f"        assert \"error\" in error_message.text.lower() or \"invalid\" in error_message.text.lower()\n\n"
                elif "success" in step_lower or "payment successful" in step_lower:
                    script += f"        # Verify success message\n"
                    script += f"        success_message = wait.until(EC.presence_of_element_located((By.ID, \"success-message\")))\n"
                    script += f"        assert success_message.is_displayed(), \"Success message should be visible\"\n"
                    script += f"        assert \"success\" in success_message.text.lower()\n\n"
                elif "discount" in step_lower:
                    script += f"        # Verify discount is applied\n"
                    script += f"        total_price = driver.find_element(By.ID, \"total-price\")\n"
                    script += f"        assert total_price.is_displayed(), \"Total price should be visible\"\n\n"
        
        # Add final assertions
        script += f"""        # Verify expected result: {test_case_info.get('expected_result', 'Test completed')}
        print("Test completed successfully")
        
    except Exception as e:
        print(f"Test failed with error: {{e}}")
        raise
    finally:
        # Cleanup
        driver.quit()

if __name__ == "__main__":
    test_checkout()
"""
        
        return script
    
    def _extract_selectors_from_prompt(self, prompt: str) -> dict:
        """Extract selectors from prompt/HTML structure."""
        selectors = {
            'name': 'customer-name',
            'email': 'customer-email',
            'address': 'customer-address',
            'discount': 'discount-code',
            'shipping_standard': 'shipping-standard',
            'shipping_express': 'shipping-express',
            'payment_credit': 'payment-credit-card',
            'payment_paypal': 'payment-paypal',
            'pay_button': 'pay-now-button'
        }
        
        # Try to extract from JSON in prompt
        try:
            # Look for HTML structure JSON
            json_match = re.search(r'\{[^{}]*"all_inputs"[^{}]*\}', prompt, re.DOTALL)
            if json_match:
                html_struct = json.loads(json_match.group())
                # Extract selectors from structure
                for inp in html_struct.get('all_inputs', []):
                    if inp.get('id'):
                        if 'name' in inp.get('name', '').lower() or 'customer' in inp.get('name', '').lower():
                            selectors['name'] = inp['id']
                        elif 'email' in inp.get('name', '').lower():
                            selectors['email'] = inp['id']
                        elif 'address' in inp.get('name', '').lower():
                            selectors['address'] = inp['id']
                        elif 'discount' in inp.get('name', '').lower() or 'coupon' in inp.get('name', '').lower():
                            selectors['discount'] = inp['id']
        except:
            pass
        
        return selectors
    
    def _extract_test_case_info(self, prompt: str) -> dict:
        """Extract test case information from prompt."""
        info = {
            'scenario': 'Checkout Test',
            'steps': [],
            'expected_result': 'Test completed successfully'
        }
        
        # Try to extract from JSON in prompt
        try:
            json_match = re.search(r'\{[^{}]*"test_scenario"[^{}]*\}', prompt, re.DOTALL)
            if json_match:
                test_case = json.loads(json_match.group())
                info['scenario'] = test_case.get('test_scenario', info['scenario'])
                info['steps'] = test_case.get('steps', info['steps'])
                info['expected_result'] = test_case.get('expected_result', info['expected_result'])
        except:
            pass
        
        return info
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Alias for generate_completion (for backward compatibility).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        return self.generate_completion(prompt, system_prompt, temperature)
    
    def generate_with_context(
        self,
        query: str,
        context: list,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text with RAG context.
        
        Args:
            query: User query
            context: List of context dictionaries with 'text' and optionally 'metadata'
            system_prompt: Optional system prompt
            
        Returns:
            Generated text grounded in context
        """
        # Build context string from provided context
        context_texts = []
        for i, ctx in enumerate(context):
            text = ctx.get('text', '')
            metadata = ctx.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            
            context_texts.append(f"[Source: {source}]\n{text}")
        
        context_str = "\n\n---\n\n".join(context_texts)
        
        # Build prompt with context
        prompt = f"""Based on the following context documents, please answer the query.

Context Documents:
{context_str}

Query: {query}

Please provide a detailed answer based only on the information provided in the context documents above. If the context does not contain enough information to answer the query, please state that clearly."""
        
        return self.generate_completion(prompt, system_prompt)


# Alias for backward compatibility
LLMClient = DummyLLMClient
