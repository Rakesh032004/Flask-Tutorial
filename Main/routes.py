from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
from Main import db
import requests  # For sending files to the Colab server
from Main.models import get_all_users, User, insert_user,Transcription, get_all_records, PatientData,insert_patient_data, get_all_Patientrecords # Adjust the import path as needed
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from functools import wraps

# Constants
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Flask Blueprint
app_routes = Blueprint('app_routes', __name__)

#Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # Check if the user is logged in
            session['next_url'] = request.url  # Save the current URL to return after login
            session['alert_message'] = "Please login to continue"  # Store alert message in session
            return redirect(url_for('app_routes.login'))  # Redirect to login page
        
        return f(*args, **kwargs)
    return decorated_function
# Routes
@app_routes.route('/')
#@login_required
def index():
    return render_template('LandingPage.html')

#home 
@app_routes.route('/home')
#@login_required
def home():
    return render_template('finalHome.html')



@app_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        

        # Insert user into the database
        insert_user(username, email, password)
        
        return redirect(url_for('app_routes.login'))

    return render_template('signup.html')

@app_routes.route('/view_db')
@login_required
def view_db():
    users = get_all_users()
    return render_template('success.html', users=users)

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    alert_message = session.pop('alert_message', None)  # Get the alert message if it exists

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch user from the database
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Compare passwords
            # Store user in session
            session['user_id'] = user.id
            session['username'] = user.username

            # Redirect to the saved next URL or default to the upload page
            return redirect(url_for('app_routes.home'))


        else:
            alert_message = "Invalid username or password"  # Set alert message for login failure

    return render_template('login.html', alert_message=alert_message)



@app_routes.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Check if the file is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Send file to Colab server for processing
            response_data = send_to_colab(filepath)

            if response_data and isinstance(response_data, list) and len(response_data) > 0:
                entity = response_data[0]

                # Add the filename to entity for storing in DB
                entity["AudioFile"] = filename

                # Insert transcription into the Transcription table
                #insert_transcription(filename, entity["transcription"])

                # Insert extracted patient data into the PatientData table
                insert_patient_data(entity)

                return redirect(url_for('app_routes.view_patient_data'))
            else:
                return jsonify({"error": "Failed to process file on Colab"}), 500
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
    ngrok_url = "https://5a94-104-196-142-72.ngrok-free.app"
    url = f"{ngrok_url}/process_audio"

    with open(filepath, 'rb') as audio_file:
        files = {'file': audio_file}
        try:
            response = requests.post(url, files=files)
            if response.status_code == 200:
                tp = response.json() 
                print(tp)
                return tp
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


# @app_routes.route('/view_transcriptions')
# def view_transcriptions():
#     # Fetch all transcriptions from the database
#     transcriptions = get_all_records()
#     return render_template('view_transcriptions.html', transcriptions=transcriptions)

@app_routes.route('/view_patient_data')
@login_required
def view_patient_data():
    patient_records = get_all_Patientrecords()  # Fetch all patient records
    return render_template('view_patient_data.html', patients=patient_records)

@app_routes.route('/logout')
def logout():
    
    return render_template('index.html')

@app_routes.route('/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    # Find the patient by ID
    #print(type(patient_id))
    patient = PatientData.query.get(patient_id)
    print(patient)
    if not patient:
        return "Patient not found", 404

    # Delete the patient
    db.session.delete(patient)
    db.session.commit()
    patient_rec=get_all_Patientrecords()
    #return redirect(url_for('view_patient_data', patients= patient))  # Redirect back to the patients list page
    return render_template('/view_patient_data.html', patients=patient_rec)


@app_routes.route('/download_report/<int:patient_id>', methods=['GET'])
@login_required
def download_report(patient_id):
    # Fetch the patient's data from the database
    patient = PatientData.query.get_or_404(patient_id)

    # Create a BytesIO buffer to hold the PDF data in memory
    buffer = io.BytesIO()

    # Create a PDF canvas and add content
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, f"Patient ID: {patient.id}")
    pdf.drawString(100, 730, f"Name: {patient.name}")
    pdf.drawString(100, 710, f"Age: {patient.age}")
    pdf.drawString(100, 690, f"Symptoms: {patient.symptoms}")
    pdf.drawString(100, 670, f"Diagnosis: {patient.diagnosis}")
    pdf.drawString(100, 650, f"Treatment: {patient.treatment}")

    # Finalize the PDF and save it to the buffer
    pdf.save()

    # Go back to the beginning of the BytesIO buffer
    buffer.seek(0)

    # Send the generated PDF file as a response for download
    return send_file(buffer, as_attachment=True, download_name=f"patient_{patient_id}_report.pdf", mimetype='application/pdf')