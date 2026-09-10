from typing import Dict, Any

def contextualize(metadata: Dict[str, Any], text: str) -> str:
    """
    Prepends a header to the chunk for better embedding context.
    Format: [{act_or_court}, {section_or_citation}, Jurisdiction: {jurisdiction}]
    """
    act_or_court = metadata.get("act_or_court", "Unknown")
    section = metadata.get("section_or_citation", "Unknown")
    jurisdiction = metadata.get("jurisdiction", "Unknown")
    
    header = f"[{act_or_court}, {section}, Jurisdiction: {jurisdiction}]"
    
    return f"{header}\n{text}"
