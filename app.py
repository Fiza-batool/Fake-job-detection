from flask import Flask, jsonify
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.detect_routes import detect_bp
from routes.admin_routes import admin_bp  # FR9: NEW

app = Flask(__name__)

# ========================================
# CORS Configuration
# ========================================
CORS(app, resources={r"/*": {"origins": "*"}})

# ========================================
# Register Blueprints
# ========================================
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(detect_bp, url_prefix="/job")
app.register_blueprint(admin_bp, url_prefix="/admin")  # FR9: NEW

# ========================================
# Root Route
# ========================================
@app.route("/")
def home():
    return jsonify({
        "message": "AI-Based Fake Job Detection Backend",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "authentication": [
                "POST /auth/register",
                "POST /auth/login"
            ],
            "detection": [
                "POST /job/detect/text",
                "POST /job/detect/image",
                "POST /job/verify/url",
                "GET /job/health"
            ],
            "admin": [                          # FR9: NEW
                "POST /admin/login",
                "GET /admin/stats",
                "GET /admin/detections",
                "GET /admin/reports",
                "GET /admin/audit-logs",
                "GET /admin/health"
            ]
        }
    }), 200

# ========================================
# Error Handlers (Optional but Recommended)
# ========================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested URL was not found on the server"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on the server"
    }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": "Bad request",
        "message": "The server could not understand the request"
    }), 400

# ========================================
# Run Server
# ========================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI-Based Fake Job Detection Backend Starting...")
    print("=" * 60)
    print("📍 Server: http://127.0.0.1:5000")
    print("📍 Health: http://127.0.0.1:5000/job/health")
    print("📍 Admin:  http://127.0.0.1:5000/admin/health")  # FR9: NEW
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)