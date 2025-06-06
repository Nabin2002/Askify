# main.py 
import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from threading import Thread 
import time 


from flashcard_generator import generate_flashcards
from qna_generator import generate_questions_answers, answer_question_from_context 
from summary_generator import generate_summary 
from mindmap_generator import generate_mind_map_data


from mistral_response import (
    extract_text_with_ocr, 
    sentence_based_chunking, 
    add_chunks_to_global_faiss, 
    search_global_faiss_index, 
    load_global_faiss_index 
)

app = Flask(__name__) 
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}


document_data = {} 


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.before_request
def load_faiss_on_startup():
    print("Ensuring FAISS index is loaded on app startup via mistral_response.")
    load_global_faiss_index() 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        document_id = str(uuid.uuid4()) 
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{document_id}_{filename}")
        file.save(filepath)

        
        try:
            full_text = extract_text_with_ocr(filepath)
            if full_text.startswith("Error"): 
                raise Exception(full_text)
            
            
            document_data[document_id] = {
                'full_text': full_text,
                'summary': None 
            }

            
            def process_and_index_document_async(doc_id, text_content, original_filename):
                print(f"Starting chunking and indexing for document {doc_id} in background...")
                try:
                    chunks = sentence_based_chunking(text_content)
                    if chunks:
                        add_chunks_to_global_faiss(chunks, doc_id, original_filename)
                        print(f"Document {doc_id} chunks indexed successfully.")
                    else:
                        print(f"No chunks generated for document {doc_id}.")
                except Exception as e:
                    print(f"Error during background indexing for document {doc_id}: {e}")

            
            def generate_summary_async(doc_id, text_content):
                print(f"Starting summary generation for document {doc_id} in background...")
                try:
                    summary_text = generate_summary(text_content)
                    if summary_text and not summary_text.startswith("Could not generate"): 
                        document_data[doc_id]['summary'] = summary_text
                        print(f"Summary generated for document {doc_id}.")
                    else:
                        print(f"Failed to generate summary for document {doc_id}: {summary_text}")
                except Exception as e:
                    print(f"Error generating summary for document {doc_id}: {e}")

            
            thread_indexing = Thread(target=process_and_index_document_async, args=(document_id, full_text, filename))
            thread_indexing.start()
            
            thread_summary = Thread(target=generate_summary_async, args=(document_id, full_text))
            thread_summary.start() 

            return jsonify({"message": "File uploaded and processing (OCR, chunking, indexing, summary) started in background!", "document_id": document_id})
        except Exception as e:
            print(f"Error processing document {filename}: {e}")
            return jsonify({"error": f"Error processing document: {e}"}), 500
    return jsonify({"error": "File type not allowed"}), 400


@app.route('/generate_summary/<document_id>', methods=['GET'])
def get_summary(document_id):
    if document_id not in document_data:
        return jsonify({"error": "Document not found or not processed."}), 404
    
    
    summary = document_data[document_id]['summary']
    
    if summary:
        return jsonify({"summary": summary})
    else:
        
        print(f"Summary not found for {document_id}, attempting synchronous generation...")
        text_content = document_data[document_id]['full_text']
        try:
            summary = generate_summary(text_content)
            if summary and not summary.startswith("Could not generate"):
                document_data[document_id]['summary'] = summary 
                return jsonify({"summary": summary})
            else:
                return jsonify({"error": f"Failed to generate summary: {summary}"}), 500
        except Exception as e:
            print(f"Error generating summary for {document_id}: {e}")
            return jsonify({"error": f"Error generating summary: {e}"}), 500


@app.route('/generate_flashcards/<document_id>', methods=['GET'])
def get_flashcards(document_id):
    if document_id not in document_data or document_data[document_id]['summary'] is None:
        return jsonify({"error": "Document summary not found or not processed. Please wait for processing to complete or generate summary first."}), 404
    
    
    text_content = document_data[document_id]['summary']
    
    try:
        flashcards = generate_flashcards(text_content)
        return jsonify({"flashcards": flashcards})
    except Exception as e:
        print(f"Error generating flashcards for {document_id}: {e}")
        return jsonify({"error": f"Error generating flashcards: {e}"}), 500


@app.route('/generate_qna/<document_id>', methods=['GET'])
def get_qna(document_id):
    if document_id not in document_data or document_data[document_id]['summary'] is None:
        return jsonify({"error": "Document summary not found or not processed. Please wait for processing to complete or generate summary first."}), 404
    
   
    text_content = document_data[document_id]['summary'] 
    
    try:
        qa_pairs = generate_questions_answers(text_content)
        return jsonify({"qa_pairs": qa_pairs})
    except Exception as e:
        print(f"Error generating general Q&A for {document_id}: {e}")
        return jsonify({"error": f"Error generating Q&A: {e}"}), 500

# Route for generating mind map
@app.route('/generate_mindmap/<document_id>', methods=['GET'])
def get_mindmap(document_id):
    if document_id not in document_data: 
        return jsonify({"error": "Document not found or not processed. Please wait for processing to complete."}), 404
    

    #text_content = document_data[document_id]['full_text'] 
    text_content = document_data[document_id]['summary'] 
    try:
        mind_map_data_uri = generate_mind_map_data(text_content)
        return jsonify({"mind_map_data": mind_map_data_uri})
    except Exception as e:
        print(f"Error generating mind map for {document_id}: {e}")
        return jsonify({"error": f"Error generating mind map: {e}"}), 500



@app.route('/query_document/<document_id>', methods=['POST'])
def query_document(document_id):
    user_query = request.json.get('query')
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    if document_id not in document_data:
        return jsonify({"error": "Document not found or not fully processed. Please wait for indexing to complete."}), 404

    try:
        print(f"Searching FAISS for query: '{user_query}' for document {document_id}...")
        

        retrieved_chunks_text = search_global_faiss_index(user_query, k=5) 

        if not retrieved_chunks_text:
            print(f"No relevant chunks found for query '{user_query}'. Attempting to answer from full text (if context window allows).")
            
            context_for_llm = document_data[document_id]['full_text'] 
        else:
            context_for_llm = "\n---\n".join(retrieved_chunks_text)
            print(f"Retrieved {len(retrieved_chunks_text)} chunks. Context length: {len(context_for_llm.split())} words.")
            
        answer = answer_question_from_context(user_query, context_for_llm)
        
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Error querying document {document_id} with query '{user_query}': {e}")
        return jsonify({"error": f"Error processing query: {e}. Please check server logs for details."}), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        load_faiss_on_startup()

    app.run(debug=True)