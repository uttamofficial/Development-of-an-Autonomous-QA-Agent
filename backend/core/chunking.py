"""
Document chunking utilities.
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Chunk text into smaller pieces using a simple recursive character splitter approach.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters (default: 1000)
        chunk_overlap: Overlap between chunks in characters (default: 200)
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Normalize whitespace
    text = text.strip()
    
    # If text is smaller than chunk_size, return as single chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Calculate end position
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at a natural boundary
        if end < text_length:
            # Try to break at newline, period, or space
            for separator in ['\n\n', '\n', '. ', ' ', '']:
                # Look backwards from end position
                lookback_pos = end - min(chunk_overlap, end - start)
                sep_pos = text.rfind(separator, lookback_pos, end)
                
                if sep_pos != -1:
                    end = sep_pos + len(separator)
                    break
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        # Move start position with overlap
        if end >= text_length:
            break
        start = end - chunk_overlap
        start = max(start, 0)  # Ensure start doesn't go negative
    
    return chunks if chunks else [text]
