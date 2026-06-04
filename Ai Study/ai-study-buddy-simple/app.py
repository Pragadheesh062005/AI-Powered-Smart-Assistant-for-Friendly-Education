import os
import time
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Initialize Flask app
app = Flask(__name__)

# 3. Define Upload folder absolutely relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 4. Global variable to store uploaded file object (Gemini File API)
uploaded_file = None

@app.route("/", methods=["GET"])
def index():
    """
    Renders the main page.
    """
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Handles PDF file uploads.
    Uploads the PDF to Google Gemini File API.
    """
    global uploaded_file
    
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400
        
    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file!"}), 400
        
    try:
        # Save temporary file
        filename = secure_filename(file.filename)
        if not filename:
            filename = "uploaded_file.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Import and configure GenAI
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Upload to GenAI
        gemini_file = genai.upload_file(file_path)
        
        # Wait for processing with timeout (expanded to 10 minutes to support large documents)
        attempts = 0
        max_attempts = 300  # 600 seconds (10 minutes)
        while gemini_file.state.name == "PROCESSING" and attempts < max_attempts:
            time.sleep(2)
            gemini_file = genai.get_file(gemini_file.name)
            attempts += 1
            
        if gemini_file.state.name == "PROCESSING":
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": "Processing timed out"}), 500
            
        # Clean up local file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        if gemini_file.state.name == "FAILED":
            return jsonify({"error": "Failed to process PDF on Gemini API."}), 500
            
        uploaded_file = gemini_file
        
        return jsonify({"message": "PDF successfully uploaded and processed!"})
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            return jsonify({"error": "Invalid API Key. Please check your .env file."}), 401
        return jsonify({"error": f"Error processing PDF: {error_msg}"}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    """
    Answers questions using Gemini AI.
    """
    global uploaded_file
    
    data = request.get_json()
    question = data.get("question")
    
    if not question:
        return jsonify({"error": "Question cannot be empty!"}), 400
        
    if not uploaded_file:
        return jsonify({"error": "Please upload a PDF first before asking questions!"}), 400
        
    try:
        # Import and configure GenAI
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create our prompt
        sys_instructions = "System Instructions: You are a helpful AI - POWERED SMART ASSISTANT FOR FRIENDLY EDUCATION. ONLY answer based on the provided document context. If the answer is not in the context, say so."
        prompt = f"{sys_instructions}\n\nUser Question: '{question}'"
        
        # Ask Google Gemini AI
        response = model.generate_content([uploaded_file, prompt])
        
        return jsonify({"answer": response.text})
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            return jsonify({"error": "Invalid API Key. Please check your .env file."}), 401
        return jsonify({"error": f"Error communicating with AI: {error_msg}"}), 500

if __name__ == "__main__":
    # Run the server
    app.run(debug=True, port=5000)
