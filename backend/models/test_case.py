"""
Pydantic models for test case structures.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class TestCase(BaseModel):
    """Test case model."""
    test_id: str = Field(description="Unique test case ID")
    feature: str = Field(description="Feature being tested")
    test_scenario: str = Field(description="Test scenario description")
    preconditions: Optional[str] = Field(
        description="Preconditions for the test",
        default=None
    )
    steps: List[str] = Field(description="Test steps")
    expected_result: str = Field(description="Expected result")
    test_type: str = Field(
        description="Test type (positive/negative/boundary/etc.)",
        default="positive"
    )
    grounded_in: List[str] = Field(
        description="List of source document names that this test case is based on",
        default_factory=list
    )


class TestCaseRequest(BaseModel):
    """Request model for test case generation."""
    query: str = Field(
        description="User query, e.g., 'Generate all positive and negative test cases for the discount code feature.'"
    )


class TestCaseResponse(BaseModel):
    """Response model for test case generation."""
    test_cases: List[TestCase] = Field(description="List of generated test cases")


# Keep old models for backward compatibility if needed
class TestCaseGenerationRequest(BaseModel):
    """Request model for test case generation (legacy)."""
    query: str = Field(description="User query or requirements")
    max_test_cases: int = Field(
        description="Maximum number of test cases to generate",
        default=10
    )


class SeleniumScriptRequest(BaseModel):
    """Request model for Selenium script generation."""
    test_case: Dict = Field(description="Test case dictionary")
    checkout_html_path: str = Field(description="Path to checkout.html")
