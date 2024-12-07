from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
import requests  # For sending files to the Colab server
from Main.models import insert_user, get_all_users, User, Transcription, get_all_records, insert_transcription, PatientData,insert_patient_data, get_all_Patientrecords # Adjust the import path as needed

# Constants
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Flask Blueprint
app_routes = Blueprint('app_routes', __name__)

# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app_routes.route('/')
def index():
    return render_template('LandingPage.html')

@app_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Insert user into the database
        insert_user(username, email, password)
        return redirect(url_for('app_routes.upload_file'))

    return render_template('signup.html')

@app_routes.route('/view_db')
def view_db():
    users = get_all_users()
    return render_template('success.html', users=users)

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch user from the database
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Compare passwords
            # Valid credentials
            return redirect(url_for('app_routes.upload_file'))
        else:
            # Invalid credentials
            flash('Invalid username or password', 'error')
            return render_template('login.html')  # Re-render login page with error

    return render_template('login.html')

@app_routes.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Check if the file is allowed
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save the file to the 'uploads' folder
            file.save(filepath)
            
            # Send the file to Colab for transcription and data extraction
            response_data = send_to_colab(filepath)
            
            if response_data and isinstance(response_data, list) and len(response_data) > 0:
                entity = response_data[0]  # Extract dictionary at index 0

                # Add AudioFile field to the dictionary
                entity["AudioFile"] = filename
                
                # Insert the data into the database
                insert_patient_data(entity)
                
                return redirect(url_for('app_routes.view_transcriptions'))
            else:
                return jsonify({"error": "Failed to process the file on Colab"}), 500

        else:
            return jsonify({"error": "Invalid file format"}), 400

    return render_template('upload.html')



@app_routes.route('/check-unique', methods=['POST'])
def check_unique():
    """Checks if a username or email is unique."""
    username = request.json.get('username', None)
    email = request.json.get('email', None)

    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({"exists": True, "field": "username"})
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({"exists": True, "field": "email"})

    return jsonify({"exists": False})

# Function to send the audio file to Colab
def send_to_colab(filepath):
    ngrok_url = "https://594b-34-75-111-27.ngrok-free.app"
    url = f"{ngrok_url}/process_audio"

    with open(filepath, 'rb') as audio_file:
        files = {'file': audio_file}
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                tp = response.json() 
                print(tp)
                # Should be a list with a dictionary at index 0
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            return None
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return None


@app_routes.route('/view_transcriptions')
def view_transcriptions():
    # Fetch all transcriptions from the database
    transcriptions = get_all_records()
    return render_template('view_transcriptions.html', transcriptions=transcriptions)

@app_routes.route('/view_patient_data')
def view_patient_data():
    patient_records = get_all_Patientrecords()  # Fetch all patient records
    return render_template('view_patient_data.html', patients=patient_records)
