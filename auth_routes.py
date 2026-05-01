"""
Authentication Routes for Fake Job Detection System
FR1: User Registration and Login
Backend/routes/auth_routes.py
"""

from flask import Blueprint, request, jsonify
from database.db import get_users_collection   # ✅ MongoDB use ho rahi hai
from config import config                       # ✅ config.py se SECRET_KEY aa rahi hai
import bcrypt
import jwt
import re
from datetime import datetime, timedelta

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# ✅ SECRET_KEY sirf ek jagah se aa rahi hai — config.py se
SECRET_KEY = config.SECRET_KEY


# ========================================
# Helper Functions
# ========================================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength
    Minimum 8 characters, at least 1 uppercase, 1 number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter"

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number"

    return True, "Password is strong"


def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, hashed_password):
    """Verify password against hashed password"""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_jwt_token(user_data):
    """Generate JWT token"""
    payload = {
        'email': user_data['email'],
        'name': user_data['name'],
        'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


# ========================================
# FR1: User Registration
# ========================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration Endpoint

    Request Body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "SecurePass123",
        "confirmPassword": "SecurePass123"
    }
    """
    try:
        data = request.get_json()

        print(f"📥 Registration request: {data}")

        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400

        if not data.get('email'):
            return jsonify({'success': False, 'error': 'Email is required'}), 400

        if not data.get('password'):
            return jsonify({'success': False, 'error': 'Password is required'}), 400

        # Accept both camelCase and snake_case for confirm password
        confirm_password = (
            data.get('confirmPassword') or
            data.get('confirm_password') or
            data.get('password')
        )

        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']

        # Validate name
        if len(name) < 2:
            return jsonify({'success': False, 'error': 'Name must be at least 2 characters'}), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400

        # Validate passwords match
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'error': message}), 400

        # ✅ MongoDB se check karo — email already registered hai?
        users_col = get_users_collection()

        if users_col is None:
            return jsonify({
                'success': False,
                'error': 'Database not connected. Please start MongoDB.'
            }), 500

        existing_user = users_col.find_one({'email': email})
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Email already registered. Please login instead.'
            }), 400

        # Hash password
        hashed_password = hash_password(password)

        # ✅ MongoDB mein save karo
        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.utcnow().isoformat(),
            'role': 'user'
        }

        users_col.insert_one(user_data)

        # Generate JWT token
        token = generate_jwt_token(user_data)

        print(f"✅ User registered in MongoDB: {email}")

        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'token': token,
            'user': {
                'name': name,
                'email': email
            }
        }), 201

    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return jsonify({'success': False, 'error': f'Registration failed: {str(e)}'}), 500


# ========================================
# FR1: User Login
# ========================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login Endpoint

    Request Body:
    {
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    """
    try:
        data = request.get_json()

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400

        email = data['email'].strip().lower()
        password = data['password']

        # Validate email format
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400

        # ✅ MongoDB se user dhundo
        users_col = get_users_collection()

        if users_col is None:
            return jsonify({
                'success': False,
                'error': 'Database not connected. Please start MongoDB.'
            }), 500

        user = users_col.find_one({'email': email})

        if not user:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

        # Verify password
        if not verify_password(password, user['password']):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

        # Generate JWT token
        token = generate_jwt_token(user)

        print(f"✅ User logged in: {email}")

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'name': user['name'],
                'email': user['email']
            }
        }), 200

    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'error': f'Login failed: {str(e)}'}), 500


# ========================================
# Token Verification
# ========================================
@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token validity"""
    try:
        data = request.get_json()

        if not data or 'token' not in data:
            return jsonify({'success': False, 'error': 'Token is required'}), 400

        payload, error = verify_jwt_token(data['token'])

        if error:
            return jsonify({'success': False, 'error': error}), 401

        return jsonify({
            'success': True,
            'valid': True,
            'user': {
                'name': payload['name'],
                'email': payload['email']
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# Get Current User
# ========================================
@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info from token"""
    try:
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'No token provided'}), 401

        token = auth_header.split(' ')[1]
        payload, error = verify_jwt_token(token)

        if error:
            return jsonify({'success': False, 'error': error}), 401

        # ✅ MongoDB se user info lo
        users_col = get_users_collection()
        user = users_col.find_one({'email': payload['email']})

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        return jsonify({
            'success': True,
            'user': {
                'name': user['name'],
                'email': user['email'],
                'created_at': user.get('created_at', '')
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500