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

def insert_user(username, email, password):
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()

def get_all_users():
    return User.query.all()


def insert_transcription(filename, transcription):
    """Insert the file name and transcription into the database."""
    new_transcription = Transcription(file_name=filename, transcription=transcription)
    db.session.add(new_transcription)
    db.session.commit()

def get_all_records():
    return Transcription.query.all()
    
