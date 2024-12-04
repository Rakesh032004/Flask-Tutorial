from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transcription.db'  # SQLite database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        from Main.models import User, Transcription # Import models
        db.create_all()  # Ensure tables are created

    # Register blueprints
    from Main.routes import app_routes
    app.register_blueprint(app_routes)

    return app