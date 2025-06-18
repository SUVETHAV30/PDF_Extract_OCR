# Your existing imports
from mistralai import Mistral
from pathlib import Path
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
import json

# NEW: Import the organizer function
from ocr_organizer import process_ocr_response

# Your existing OCR processing code remains the same
api_key = ""
client = Mistral(api_key=api_key)

pdf_file = Path(r"C:\Users\MEGHA\OneDrive\Desktop\AIProj\pdf_to_html\pdf_html_convertor\test4.pdf")
assert pdf_file.is_file()

uploaded_file = client.files.upload(
    file={
        "file_name": pdf_file.stem,
        "content": pdf_file.read_bytes(),
    },
    purpose="ocr",
)

signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

pdf_response = client.ocr.process(
    document=DocumentURLChunk(document_url=signed_url.url),
    model="mistral-ocr-latest",
    include_image_base64=True
)

response_dict = json.loads(pdf_response.model_dump_json())

# NEW: Add this line to process and organize the data
organized_data = process_ocr_response(response_dict, str(pdf_file))

print("Processing completed! Check the generated files.")