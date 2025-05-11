# from mistralai import Mistral
# from content_processor import clean_extracted_text


# client = Mistral(api_key=API_KEY)

# # --- OCR extraction ---
# uploaded_pdf = client.files.upload(
#     file={
#         "file_name": "Question paper .pdf",
#         "content": open("Question paper .pdf", "rb"),
#     },
#     purpose="ocr"
# )
# signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

# ocr_response = client.ocr.process(
#     model="mistral-ocr-latest",
#     document={
#         "type": "document_url",
#         "document_url": signed_url.url,
#     }
# )

# # --- Collect extracted markdown text ---
# extracted_text = "\n\n".join([page.markdown for page in ocr_response.pages])

# # --- Clean the extracted content ---
# cleaned_text = clean_extracted_text(extracted_text)

# # --- Display the cleaned text ---
# print(cleaned_text)
from mistral_response import extract_text_with_ocr

from flask import Flask, request, render_template
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return "No file part", 400

    file = request.files['pdf_file']

    if file.filename == '':
        return "No selected file", 400

    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        # return f"File uploaded successfully to {file_path}"
        result = extract_text_with_ocr(file_path)
        return f"OCR Result:<br><pre>{result}</pre>"
        # print(file_path)
   
    return "Invalid file format. Please upload a PDF.", 400
if __name__ == '__main__':
    app.run(debug=True)
