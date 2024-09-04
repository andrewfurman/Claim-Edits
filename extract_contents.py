import requests
from io import BytesIO
from pdfplumber import open as open_pdf

def extract_text_from_pdf(url: str) -> str:
    response = requests.get(url)
    with open_pdf(BytesIO(response.content)) as pdf:
        all_text = ""
        for i, page in enumerate(pdf.pages, start=1):
            extracted_text = page.extract_text()
            cleaned_text = '\n'.join([line.strip() for line in extracted_text.split('\n') if line.strip()])
            all_text += f"🅿️ Start of Page {i}\n{cleaned_text}\n"
    return all_text