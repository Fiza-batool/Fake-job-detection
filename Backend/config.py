"""
Configuration file for Flask app
Backend/config.py
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""

    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    # ✅ FIX: default ab 'False' hai. Local testing ke liye .env mein
    # FLASK_DEBUG=True rakh sakti ho, lekin production (Render/Railway) mein
    # ye OFF rehna chahiye — debug mode error pages mein sensitive code dikha deta hai.
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    PORT = int(os.getenv('FLASK_PORT', 5000))

    # MongoDB Settings
    # ✅ Ye already .env se aata hai — deploy ke waqt MONGO_URI ko
    # MongoDB Atlas ki connection string se replace karna hoga.
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'jobdetect')

    # JWT Settings
    JWT_EXPIRATION_HOURS = 24

    # File Upload Settings
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # Model Settings
    MODEL_PATH = 'models/fake_job_model.pkl'
    VECTORIZER_PATH = 'models/tfidf_vectorizer.pkl'
    METADATA_PATH = 'models/model_metadata.pkl'


# Export config
config = Config()