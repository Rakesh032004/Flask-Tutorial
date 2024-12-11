from Main import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Transcription(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    transcription = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class PatientData(db.Model):
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(10), nullable=True)  # To account for unknown or empty age
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.String(255), nullable=False, default="Unknown")
    treatment = db.Column(db.String(255), nullable=False, default="No treatment available")
    audio_file = db.Column(db.String(255), nullable=True)

def insert_user(username, email, password):
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()

def get_all_users():
    return User.query.all()


# def insert_transcription(filename, transcription):
#     """Insert the file name and transcription into the database."""
#     new_transcription = Transcription(file_name=filename, transcription=transcription)
#     db.session.add(new_transcription)
#     db.session.commit()

def get_all_records():
    return Transcription.query.all()
    
from Main.models import PatientData, db

import uuid

def generate_patient_id():
    return str(uuid.uuid4())  # Generates a unique ID

# After getting the transcription data
def insert_patient_data(entity):
    """Insert a single patient record into the database."""
    record = PatientData(
        name=entity.get("Name", "Unknown"),
        age=entity.get("Age", ""),
        symptoms=entity.get("Symptoms", ""),
        diagnosis=entity.get("Diagnosis", "Unknown"),
        treatment=entity.get("Treatment", "No treatment available"),
        audio_file=entity.get("AudioFile", "")
    )
    db.session.add(record)
    db.session.commit()



def get_all_Patientrecords():
    return PatientData.query.all()
