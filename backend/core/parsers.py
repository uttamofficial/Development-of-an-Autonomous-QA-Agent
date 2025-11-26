"""
Document parsers for different file types.
"""
import json
import os
from pathlib import Path
from typing import Dict

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def parse_markdown(file_path: str) -> str:
    """
    Parse markdown file.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Extracted text content
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_text(file_path: str) -> str:
    """
    Parse plain text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Text content
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_json(file_path: str) -> str:
    """
    Parse JSON file and flatten keys/values into text.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Flattened text representation of JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    def flatten_json(obj, parent_key='', sep=': '):
        """Recursively flatten JSON into text."""
        items = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}.{key}" if parent_key else key
                if isinstance(value, (dict, list)):
                    items.extend(flatten_json(value, new_key, sep))
                else:
                    items.append(f"{new_key}{sep}{value}")
        elif isinstance(obj, list):
            for idx, value in enumerate(obj):
                new_key = f"{parent_key}[{idx}]" if parent_key else f"[{idx}]"
                if isinstance(value, (dict, list)):
                    items.extend(flatten_json(value, new_key, sep))
                else:
                    items.append(f"{new_key}{sep}{value}")
        else:
            items.append(f"{parent_key}{sep}{obj}")
        
        return items
    
    flattened = flatten_json(data)
    return '\n'.join(flattened)


def parse_pdf(file_path: str) -> str:
    """
    Parse PDF file using PyMuPDF (fitz).
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        ImportError: If PyMuPDF is not installed
    """
    if fitz is None:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF parsing. "
            "Install it with: pip install pymupdf"
        )
    
    doc = fitz.open(file_path)
    text_parts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(text)
    
    doc.close()
    return '\n\n'.join(text_parts)


def parse_html(file_path: str) -> str:
    """
    Parse HTML file and extract visible text using BeautifulSoup.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        Extracted visible text content
        
    Raises:
        ImportError: If BeautifulSoup is not installed
    """
    if BeautifulSoup is None:
        raise ImportError(
            "BeautifulSoup4 is required for HTML parsing. "
            "Install it with: pip install beautifulsoup4"
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and clean up whitespace
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up excessive newlines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def parse_file(file_path: str) -> str:
    """
    Generic file parser that picks the appropriate parser based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file extension is not supported
        FileNotFoundError: If file does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get file extension
    ext = Path(file_path).suffix.lower()
    
    # Map extensions to parsers
    parser_map = {
        '.md': parse_markdown,
        '.markdown': parse_markdown,
        '.txt': parse_text,
        '.json': parse_json,
        '.pdf': parse_pdf,
        '.html': parse_html,
        '.htm': parse_html,
    }
    
    if ext not in parser_map:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported types: {', '.join(parser_map.keys())}"
        )
    
    parser = parser_map[ext]
    return parser(file_path)
