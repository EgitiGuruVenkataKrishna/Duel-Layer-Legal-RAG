import fitz
import re
import os
from typing import List, Dict, Any

class LegalPDFParser:
    """
    Parses Legal PDFs, extracting text and metadata (Act, Chapter, Section, Subsection)
    using regex boundaries to preserve legal metadata hierarchy.
    """
    def __init__(self):
        # Extract CHAPTER headers
        self.chapter_pattern = re.compile(r'CHAPTER\s+[IVXLCDM]+', re.IGNORECASE)
        # Indian acts usually start sections with "103. " or "45A. " at the beginning of a block
        self.section_pattern = re.compile(r'^(?:Section\s+)?(\d+[A-Z]?)\.\s', re.IGNORECASE)
        self.subsection_pattern = re.compile(r'^\((\d+|[a-z])\)')

    def parse_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Reads a PDF file and constructs standard dict chunks with hierarchy preservation.
        Returns a list of dicts:
        {"Act": act_name, "Chapter": chapter_num, "Section": section_num, "Sub_section": sub_sec_num, "Page": page_num, "text": chunk_text}
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at {pdf_path}")
            
        act_name = os.path.splitext(os.path.basename(pdf_path))[0]
        chunks = []
        
        doc = fitz.open(pdf_path)
        current_chapter = None
        current_section = None
        current_subsection = None
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Use "blocks" to get cleaner separation of text paragraphs in PDFs
            blocks = page.get_text("blocks")
            
            for b in blocks:
                # block_type 0 is text
                if b[6] != 0:
                    continue
                
                para = b[4].strip()
                if not para:
                    continue
                    
                # Update current metadata if patterns match in this block
                chapter_match = self.chapter_pattern.search(para)
                if chapter_match:
                    current_chapter = chapter_match.group(0)
                    # Reset section/subsection on new chapter
                    current_section = None
                    current_subsection = None
                    
                section_match = self.section_pattern.search(para)
                if section_match:
                    current_section = section_match.group(1)
                    # Reset subsection when a new section starts
                    current_subsection = None
                    
                subsection_match = self.subsection_pattern.search(para)
                if subsection_match:
                    current_subsection = subsection_match.group(0)
                
                # Inject metadata into the text itself so BM25 tokenizes the exact section number!
                augmented_text = f"[Act: {act_name} | Chapter: {current_chapter or 'Unknown'} | Section: {current_section or 'Unknown'}]\n{para}"
                
                # Append the chunk
                chunk = {
                    "Act": act_name,
                    "Chapter": current_chapter,
                    "Section": current_section,
                    "Sub_section": current_subsection,
                    "Page": page_num + 1,  # 1-indexed page numbers
                    "text": augmented_text
                }
                chunks.append(chunk)
                
        doc.close()
        return chunks

if __name__ == "__main__":
    # Test initialization
    parser = LegalPDFParser()
    print("LegalPDFParser initialized successfully.")
