import re

def clean_text(text: str) -> str:
    """
    Cleans raw PDF text by removing common boilerplate, headers, footers, 
    and extra whitespace.
    """
    # Remove page numbers like "- 1 -", "Page 1 of 10", etc.
    text = re.sub(r'(?i)^\s*(?:page|pg\.?)\s*\d+(?:\s*of\s*\d+)?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*-\s*\d+\s*-\s*$', '', text, flags=re.MULTILINE)
    
    # Remove common boilerplate letterheads (customize as needed)
    text = re.sub(r'(?i)IN THE HIGH COURT OF[^\n]+', '', text)
    text = re.sub(r'(?i)IN THE SUPREME COURT OF INDIA[^\n]*', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()
