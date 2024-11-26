from flask import Blueprint, render_template, request, redirect, url_for, flash
from Main.models import insert_user, get_all_users, User
from werkzeug.utils import secure_filename
import os

# Import the ML model function (placeholder for actual integration)
from Main.ml_model import audio_to_text

app_routes = Blueprint('app_routes', __name__)


@app_routes.route('/')
def index():
    return render_template('index.html')

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
            users = get_all_users()
            return redirect(url_for('app_routes.upload_file'))
        else:
            # Invalid credentials
            flash('Invalid username or password', 'error')
            return render_template('login.html')  # Re-render login page with error

    return render_template('login.html')  # GET request renders login page



from flask import jsonify

@app_routes.route('/check-unique', methods=['POST'])
def check_unique():
    data = request.get_json()
    print(data)
    username = data.get('username')
    email = data.get('email')

    response = {'username_exists': False, 'email_exists': False}

    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            response['username_exists'] = True

    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            response['email_exists'] = True

    return jsonify(response)



@app_routes.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if file is present in the request
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Save the file if it has an allowed extension
        if file:
            filename = secure_filename(file.filename)
            

            # Process the file using the ML model
            text_output = audio_to_text(filename)

            # Redirect to a page showing the result
            return render_template('result.html', text_output=text_output)
        else:
            flash('File type not allowed')
            return redirect(request.url)

    return render_template('upload.html')