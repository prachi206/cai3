from datetime import datetime
from flask import Flask, render_template, request, redirect, send_from_directory
import os
import google.generativeai as genai

# Configure Google Cloud Gemini API key
genai.configure(api_key="AIzaSyA_oJdAsoFZxre4OocTzE4OhH4MW9jqcY4")

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/speak'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files(folder, extension, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = []
    
    files = [filename for filename in os.listdir(folder) 
             if (filename.endswith(extension) or filename.endswith('.txt')) 
             and not any(pattern in filename for pattern in exclude_patterns)]
    
    files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    return files

@app.route('/')
def index():
    speak_files = get_files(app.config['UPLOAD_FOLDER'], '.wav')
    return render_template('index.html', speak_files=speak_files)

# Update this route to correctly handle audio uploads
@app.route('/upload', methods=['POST'])
def upload_speak():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Invalid file selection')
        return redirect(request.url)
    
    filename_base = datetime.now().strftime("%Y%m%d-%I%M%S%p")
    audio_filename = f"{filename_base}.wav"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    file.save(file_path)
    
    # Process audio with Gemini API
    analysis_result = process_audio_with_gemini(file_path)
    
    # Save analysis result (transcript + sentiment analysis)
    result_filename = f"{filename_base}.txt"
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
    with open(result_path, 'w') as f:
        f.write(analysis_result)
    
    return redirect('/')

@app.route('/uploads/speak/<path:filename>')
def speak_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/script.js')
def serve_script():
    return send_from_directory('.', 'script.js')  # Serve script.js from the current directory

def process_audio_with_gemini(file_path):
    with open(file_path, "rb") as audio_file:
        audio_data = audio_file.read()
    
    mime_type = "audio/wav" if file_path.endswith('.wav') else "audio/mpeg"
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content([ 
        "Provide the Transcription of the audio ,providing a sentimental analysis score between -1 and 1:",
        {"mime_type": mime_type, "data": audio_data}
    ])
    return response.text if response else "No analysis available"

@app.route('/script.js', methods=['GET'])
def scripts_js():
    return send_from_directory('.', 'script.js')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
