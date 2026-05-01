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
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # MongoDB Settings
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