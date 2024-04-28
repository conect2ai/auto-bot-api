import PyPDF2
from pydantic import BaseModel, Field

class QuestionParams(BaseModel):
    question: str = Field(..., title="Question")
    brand: str = Field(None, title="Brand")
    model: str = Field(None, title="Model")
    year: str = Field(None, title="Year")

class KnowledgeBaseRequest(BaseModel):
    openai_api_key: str

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF file.
    """
    text = ""
    with open(file_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text