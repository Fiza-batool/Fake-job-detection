"""
Detection Routes for Fake Job Detection System
FR2: Text Detection
FR3: Image Detection  
FR4: URL Verification
FR7: Community Reporting
FR10: Verification History
FR11: User Feedback & Model Improvement  ← NEW
"""

from flask import Blueprint, request, jsonify
import pickle
import re
import base64
import io
import pandas as pd
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from urllib.parse import urlparse
import requests
import whois
from datetime import datetime

# ========================================
# Configure Tesseract Path (WINDOWS)
# ========================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Create Blueprint
detect_bp = Blueprint('detect', __name__)

# ========================================
# THRESHOLD SETTING
# ========================================
FAKE_THRESHOLD = 30

# Load ML models at startup
MODEL_DIR = Path(__file__).parent.parent / 'models'

try:
    with open(MODEL_DIR / 'fake_job_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    with open(MODEL_DIR / 'tfidf_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    
    with open(MODEL_DIR / 'model_metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)
    
    print("✅ ML Model loaded successfully!")
    print(f"📊 Model: {metadata['best_model_name']}")
    print(f"📊 Accuracy: {metadata['accuracy']*100:.2f}%")
    print(f"📊 Fake Threshold: {FAKE_THRESHOLD}%")
    
except Exception as e:
    print(f"❌ Error loading models: {e}")
    model = None
    vectorizer = None
    metadata = None


# ========================================
# FR10: History Storage
# FR7: Reports Storage
# FR11: Feedback Storage  ← NEW
# ========================================
history_db = []
reports_db = []
feedback_db = []  # FR11: NEW


# ========================================
# Image Preprocessing for Better OCR
# ========================================
def preprocess_image_for_ocr(image):
    try:
        if image.mode != 'L':
            image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        image = image.filter(ImageFilter.SHARPEN)
        width, height = image.size
        if width < 800:
            ratio = 800 / width
            new_height = int(height * ratio)
            image = image.resize((800, new_height), Image.Resampling.LANCZOS)
        return image
    except Exception as e:
        print(f"⚠️ Image preprocessing warning: {e}")
        return image


# ========================================
# Text Preprocessing
# ========================================
def clean_text(text):
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = ' '.join(text.split())
    return text


# ========================================
# FR2: Text Detection Endpoint
# ========================================
@detect_bp.route('/detect/text', methods=['POST'])
def detect_text():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if model is None or vectorizer is None:
            return jsonify({
                'success': False,
                'error': 'Model not loaded. Please train the model first.'
            }), 500
        
        if 'job_text' in data:
            combined_text = data['job_text']
        else:
            combined_text = ' '.join([
                str(data.get('title', '')),
                str(data.get('company_profile', '')),
                str(data.get('description', '')),
                str(data.get('requirements', '')),
                str(data.get('benefits', ''))
            ])
        
        if len(combined_text.strip()) < 50:
            return jsonify({
                'success': False,
                'error': 'Text too short. Minimum 50 characters required.'
            }), 400
        
        cleaned_text = clean_text(combined_text)
        
        if not cleaned_text or len(cleaned_text.strip()) < 20:
            return jsonify({
                'success': False,
                'error': 'No valid text content after cleaning'
            }), 400
        
        features = vectorizer.transform([cleaned_text])
        probabilities = model.predict_proba(features)[0]
        fake_prob = float(probabilities[1] * 100)
        real_prob = float(probabilities[0] * 100)

        is_fake = fake_prob >= FAKE_THRESHOLD
        prediction = 'Fake' if is_fake else 'Real'
        confidence = fake_prob if is_fake else real_prob

        # ✅ FR10: History mein save karo
        history_db.append({
            'type': 'Text Detection',
            'input': combined_text[:100] + '...' if len(combined_text) > 100 else combined_text,
            'prediction': prediction,
            'risk_score': round(fake_prob, 1),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        result = {
            'success': True,
            'prediction': prediction,
            'confidence': round(confidence, 1),
            'probabilities': {
                'real': round(real_prob, 1),
                'fake': round(fake_prob, 1)
            },
            'threshold_used': FAKE_THRESHOLD,
            'model_used': metadata['best_model_name'],
            'model_accuracy': f"{metadata['accuracy']*100:.2f}%"
        }
        
        print(f"✅ Text Detection: {prediction} | Fake Prob: {fake_prob:.1f}% | History: {len(history_db)} items")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error in text detection: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Detection error: {str(e)}'
        }), 500


# ========================================
# FR3: Image Detection
# ========================================
@detect_bp.route('/detect/image', methods=['POST'])
def detect_image():
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        try:
            image_data = base64.b64decode(data['image'])
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid image format: {str(e)}'
            }), 400
        
        image = image.convert('L')
        image = ImageEnhance.Contrast(image).enhance(2)
        
        try:
            extracted_text = pytesseract.image_to_string(image)
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            ocr_confidence = sum(confidences) / len(confidences) if confidences else 0
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'OCR extraction failed: {str(e)}'
            }), 500
        
        if len(extracted_text.strip()) < 20:
            return jsonify({
                'success': False,
                'error': 'Could not extract enough text from image. Please use a clearer image.',
                'extracted_text': extracted_text,
                'ocr_confidence': ocr_confidence
            }), 400
        
        cleaned_text = clean_text(extracted_text)
        
        if len(cleaned_text.strip()) < 20:
            return jsonify({
                'success': False,
                'error': 'No meaningful text found in image',
                'extracted_text': extracted_text,
                'ocr_confidence': ocr_confidence
            }), 400
        
        features = vectorizer.transform([cleaned_text])
        probabilities = model.predict_proba(features)[0]
        fake_prob = float(probabilities[1] * 100)
        real_prob = float(probabilities[0] * 100)

        is_fake = fake_prob >= FAKE_THRESHOLD
        prediction = 'Fake' if is_fake else 'Real'
        confidence = fake_prob if is_fake else real_prob

        # ✅ FR10: History mein save karo
        history_db.append({
            'type': 'Image Detection',
            'input': f'Image: {data.get("filename", "uploaded_image")}',
            'prediction': prediction,
            'risk_score': round(fake_prob, 1),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        result = {
            'success': True,
            'prediction': prediction,
            'confidence': round(confidence, 1),
            'probabilities': {
                'real': round(real_prob, 1),
                'fake': round(fake_prob, 1)
            },
            'threshold_used': FAKE_THRESHOLD,
            'extracted_text': extracted_text,
            'ocr_confidence': float(ocr_confidence),
            'model_used': metadata['best_model_name']
        }
        
        print(f"✅ Image Detection: {prediction} | Fake Prob: {fake_prob:.1f}% | History: {len(history_db)} items")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error in image detection: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Image detection error: {str(e)}'
        }), 500


# ========================================
# FR4: URL Verification
# ========================================
@detect_bp.route('/verify/url', methods=['POST'])
def verify_url():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        url = data['url'].strip()
        
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return jsonify({
                'success': False,
                'error': 'Invalid URL format. Must start with http:// or https://'
            }), 400
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        domain_info = {}
        ssl_valid = False
        domain_age_days = 0
        is_blacklisted = False
        trust_score = 50

        try:
            response = requests.get(url, timeout=5, verify=True)
            ssl_valid = True
            trust_score += 20
        except requests.exceptions.SSLError:
            ssl_valid = False
            trust_score -= 20
        except Exception:
            pass
        
        try:
            domain_data = whois.whois(domain)
            if domain_data:
                domain_info = {
                    'domain_name': domain_data.domain_name if hasattr(domain_data, 'domain_name') else domain,
                    'registrar': domain_data.registrar if hasattr(domain_data, 'registrar') else 'Unknown',
                    'creation_date': str(domain_data.creation_date) if hasattr(domain_data, 'creation_date') else 'Unknown',
                    'expiration_date': str(domain_data.expiration_date) if hasattr(domain_data, 'expiration_date') else 'Unknown'
                }
                if hasattr(domain_data, 'creation_date') and domain_data.creation_date:
                    creation_date = domain_data.creation_date
                    if isinstance(creation_date, list):
                        creation_date = creation_date[0]
                    domain_age_days = (datetime.now() - creation_date).days
                    if domain_age_days > 365:
                        trust_score += 20
                    elif domain_age_days > 180:
                        trust_score += 10
                    else:
                        trust_score -= 10
        except Exception as e:
            domain_info = {'error': f'WHOIS lookup failed: {str(e)}'}
        
        suspicious_keywords = ['free-job', 'fake', 'scam', 'urgent-hire', 'easy-money']
        if any(keyword in domain.lower() for keyword in suspicious_keywords):
            is_blacklisted = True
            trust_score -= 30
        
        risk_score = max(0, min(100, 100 - trust_score))
        is_safe = trust_score >= 60

        # ✅ FR10: History mein save karo
        history_db.append({
            'type': 'URL Verification',
            'input': url,
            'prediction': 'Safe' if is_safe else 'Suspicious',
            'risk_score': risk_score,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        result = {
            'success': True,
            'is_safe': is_safe,
            'risk_score': risk_score,
            'trust_score': trust_score,
            'domain_info': domain_info,
            'ssl_status': 'Valid' if ssl_valid else 'Invalid',
            'domain_age': domain_age_days,
            'is_blacklisted': is_blacklisted
        }
        
        print(f"✅ URL: {'Safe' if is_safe else 'Unsafe'} | Trust: {trust_score}% | History: {len(history_db)} items")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error in URL verification: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'URL verification error: {str(e)}'
        }), 500


# ========================================
# FR7: Community Reporting
# ========================================
@detect_bp.route('/report', methods=['POST'])
def report_job():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        reason = data.get('reason', '').strip()
        if not reason:
            return jsonify({'success': False, 'error': 'Please select a reason'}), 400
        
        valid_reasons = [
            'Payment Required',
            'Personal Information Theft',
            'Fake Company',
            'Too Good To Be True',
            'Suspicious URL',
            'Duplicate Posting',
            'Other'
        ]
        
        if reason not in valid_reasons:
            return jsonify({'success': False, 'error': 'Invalid reason selected'}), 400
        
        description = data.get('description', '').strip()
        if len(description) < 10:
            return jsonify({'success': False, 'error': 'Description must be at least 10 characters'}), 400
        if len(description) > 500:
            return jsonify({'success': False, 'error': 'Description must be less than 500 characters'}), 400
        
        job_text = data.get('job_text', '').strip()
        job_url  = data.get('url', '').strip()
        
        for existing_report in reports_db:
            if job_url and existing_report.get('url') == job_url:
                return jsonify({'success': False, 'error': 'This job has already been reported'}), 400
            if job_text and existing_report.get('job_text', '')[:100] == job_text[:100]:
                return jsonify({'success': False, 'error': 'This job has already been reported'}), 400
        
        report = {
            'id': f"RPT-{len(reports_db) + 1001}",
            'reason': reason,
            'description': description,
            'job_text': job_text,
            'url': job_url,
            'reported_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        reports_db.append(report)
        print(f"📢 New Report: {report['id']} - Reason: {reason}")
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully! Thank you for helping the community.',
            'report_id': report['id'],
            'status': 'pending'
        }), 201
        
    except Exception as e:
        print(f"❌ Error in reporting: {str(e)}")
        return jsonify({'success': False, 'error': f'Report error: {str(e)}'}), 500


@detect_bp.route('/reports', methods=['GET'])
def get_reports():
    try:
        return jsonify({
            'success': True,
            'total_reports': len(reports_db),
            'reports': reports_db
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR10: Verification History
# ========================================
@detect_bp.route('/history', methods=['GET'])
def get_history():
    """FR10: Get all verification history"""
    try:
        return jsonify({
            'success': True,
            'total': len(history_db),
            'history': list(reversed(history_db))  # newest first
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# Health Check
# ========================================
@detect_bp.route('/health', methods=['GET'])
def health_check():
    model_status = 'loaded' if model and vectorizer else 'not_loaded'
    return jsonify({
        'success': True,
        'status': 'healthy',
        'model_status': model_status,
        'model_name': metadata['best_model_name'] if metadata else 'Unknown',
        'accuracy': f"{metadata['accuracy']*100:.2f}%" if metadata else 'N/A',
        'fake_threshold': f"{FAKE_THRESHOLD}%",
        'history_count': len(history_db)
    }), 200


# ========================================
# FR11: User Feedback & Model Improvement
# ← ALL NEW CODE — nothing above changed
# ========================================

@detect_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    FR11: Capture user feedback on detection results
    Input:  rating (thumbs_up/thumbs_down) + optional comment (max 200 chars)
    Process: validate → spam check → store with metadata → calculate accuracy metrics
    Output: confirmation + updated accuracy stats + model improvement suggestion
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # FR11 Validation 1: Rating is mandatory
        rating = data.get('rating', '').strip()
        if rating not in ['thumbs_up', 'thumbs_down']:
            return jsonify({
                'success': False,
                'error': 'Please select a rating (thumbs up or thumbs down)'
            }), 400

        # FR11 Validation 2: Comment max 200 characters
        comment = data.get('comment', '').strip()
        if len(comment) > 200:
            return jsonify({
                'success': False,
                'error': 'Comment must be less than 200 characters'
            }), 400

        # FR11 Validation 3: Spam detection — check last 10 feedbacks
        if comment:
            for existing in feedback_db[-10:]:
                if existing.get('comment', '').lower() == comment.lower():
                    return jsonify({
                        'success': False,
                        'error': 'Duplicate feedback detected. Please provide unique feedback.'
                    }), 400

        # FR11 Process: Link feedback to detection result with metadata
        detection_method = data.get('detection_method', 'Unknown')
        risk_score       = data.get('risk_score', 0)
        prediction       = data.get('prediction', 'Unknown')

        # FR11 Process: Store feedback with all metadata
        feedback_entry = {
            'id':               f"FB-{len(feedback_db) + 1001}",
            'rating':           rating,
            'comment':          comment,
            'detection_method': detection_method,
            'risk_score':       risk_score,
            'prediction':       prediction,
            'is_accurate':      rating == 'thumbs_up',
            'submitted_at':     datetime.now().isoformat()
        }
        feedback_db.append(feedback_entry)

        # FR11 Process: Calculate accuracy metrics
        total_feedback   = len(feedback_db)
        positive_ratings = sum(1 for f in feedback_db if f['rating'] == 'thumbs_up')
        negative_ratings = total_feedback - positive_ratings
        satisfaction_rate = round((positive_ratings / total_feedback) * 100, 1) if total_feedback > 0 else 0

        # FR11 Output: Model improvement suggestion based on rating
        if rating == 'thumbs_up':
            improvement_suggestion = "Detection result confirmed as accurate. This feedback helps validate our ML model performance."
        else:
            improvement_suggestion = "Thank you for flagging this. Your feedback will help retrain and improve our model accuracy in future updates."

        print(f"✅ FR11 Feedback: {rating} | Total: {total_feedback} | Satisfaction: {satisfaction_rate}%")

        # FR11 Output: Return confirmation + updated accuracy stats
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback! It helps improve our detection accuracy.',
            'feedback_id': feedback_entry['id'],
            'accuracy_metrics': {
                'total_feedback':       total_feedback,
                'positive_ratings':     positive_ratings,
                'negative_ratings':     negative_ratings,
                'user_satisfaction_rate': satisfaction_rate
            },
            'model_improvement_suggestion': improvement_suggestion
        }), 201

    except Exception as e:
        print(f"❌ FR11 Feedback error: {str(e)}")
        return jsonify({'success': False, 'error': f'Feedback error: {str(e)}'}), 500


@detect_bp.route('/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """FR11: Get feedback statistics for feedback.html dashboard"""
    try:
        total = len(feedback_db)

        if total == 0:
            return jsonify({
                'success':           True,
                'total_feedback':    0,
                'positive_ratings':  0,
                'negative_ratings':  0,
                'satisfaction_rate': 0,
                'feedback':          []
            }), 200

        positive     = sum(1 for f in feedback_db if f['rating'] == 'thumbs_up')
        negative     = total - positive
        satisfaction = round((positive / total) * 100, 1)

        return jsonify({
            'success':           True,
            'total_feedback':    total,
            'positive_ratings':  positive,
            'negative_ratings':  negative,
            'satisfaction_rate': satisfaction,
            'feedback':          list(reversed(feedback_db))  # newest first
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500