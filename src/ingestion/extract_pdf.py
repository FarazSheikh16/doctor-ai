import PyPDF2

def extract_text_from_pdf(pdf_path):
    text_chunks = []
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()  
            text_chunks.append({
                "page_num": page_num + 1,  
                "content": text if text else ""  
            })
    return text_chunks

