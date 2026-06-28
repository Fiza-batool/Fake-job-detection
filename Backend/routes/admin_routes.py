"""
Admin Routes for Fake Job Detection System
FR9: Manual Database Management (Admin)

FR9 Requirements:
- Input:  Admin credentials + MongoDB interface
- Validation: Admin authentication & authorization, data type validation,
              operation permissions check
- Process: Secure admin authentication, database connection,
           CRUD operations, data validation, operation logging & audit trails
- Output: Database operation confirmations, error messages,
          audit log entries, backup completion status
"""

import os
from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from database.db import (
    get_detection_history_collection,
    get_reports_collection,
    get_feedback_collection,
    get_audit_logs_collection
)

# Create Admin Blueprint
admin_bp = Blueprint('admin', __name__)

# ========================================
# FR9: Admin Credentials
# ✅ FIX: pehle yahan "admin" / "admin123" plain text mein hardcoded thay.
# Ab .env (ya hosting platform ke environment variables) se aate hain.
# Deploy karte waqt ADMIN_USERNAME aur ADMIN_PASSWORD zaroor set karo,
# warna neeche wali default (asaan-se-guess-honay-wali) values use hongi.
# ========================================
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def _serialize(doc):
    """MongoDB ke ObjectId ko string mein convert karta hai (JSON-safe)"""
    if doc is None:
        return None
    doc = dict(doc)
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc


# ========================================
# FR9: Helper — Log Admin Action
# ✅ FIX: audit_logs ab MongoDB collection mein save hote hain
# (pehle Python list mein thay, server restart pe gayab ho jate)
# ========================================
def log_admin_action(action, detail, status="success"):
    """
    FR9: Operation logging and audit trails
    Logs every admin action with timestamp and status
    """
    logs_col = get_audit_logs_collection()

    entry = {
        'action': action,
        'detail': detail,
        'status': status,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if logs_col is not None:
        result = logs_col.insert_one(entry)
        entry['id'] = f"LOG-{str(result.inserted_id)[-6:]}"
    else:
        entry['id'] = "LOG-OFFLINE"

    print(f"📋 FR9 Audit Log: [{action}] {detail} | Status: {status}")
    return entry


# ========================================
# FR9: Admin Authentication
# ========================================
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """FR9: Secure admin authentication"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400

        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            log_admin_action("Login Failed", f"Failed login attempt for username: {username}", "failed")
            return jsonify({
                'success': False,
                'error': 'Invalid admin credentials'
            }), 401

        log_admin_action("Admin Login", f"Administrator logged in successfully")

        return jsonify({
            'success': True,
            'message': 'Admin authenticated successfully',
            'admin': username
        }), 200

    except Exception as e:
        print(f"❌ Admin login error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Get System Statistics
# ✅ FIX: ab MongoDB collections se count hota hai
# (pehle routes.detect_routes se Python lists import hoti thi)
# ========================================
@admin_bp.route('/stats', methods=['GET'])
def get_admin_stats():
    """FR9: Get overall system statistics for admin dashboard"""
    try:
        history_col = get_detection_history_collection()
        reports_col = get_reports_collection()
        feedback_col = get_feedback_collection()

        total_detections = history_col.count_documents({}) if history_col is not None else 0
        total_reports = reports_col.count_documents({}) if reports_col is not None else 0
        total_feedback = feedback_col.count_documents({}) if feedback_col is not None else 0

        if total_feedback > 0:
            positive = feedback_col.count_documents({'rating': 'thumbs_up'})
            satisfaction = round((positive / total_feedback) * 100, 1)
        else:
            satisfaction = 0

        fake_count = history_col.count_documents(
            {'prediction': {'$in': ['Fake', 'Suspicious']}}
        ) if history_col is not None else 0
        real_count = total_detections - fake_count

        logs_col = get_audit_logs_collection()
        audit_log_count = logs_col.count_documents({}) if logs_col is not None else 0

        log_admin_action("View Stats", "Admin accessed system statistics")

        return jsonify({
            'success': True,
            'total_detections': total_detections,
            'total_reports': total_reports,
            'total_feedback': total_feedback,
            'satisfaction_rate': satisfaction,
            'fake_detections': fake_count,
            'real_detections': real_count,
            'audit_log_count': audit_log_count
        }), 200

    except Exception as e:
        print(f"❌ Admin stats error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: View Detection History (CRUD - Read)
# ========================================
@admin_bp.route('/detections', methods=['GET'])
def get_all_detections():
    """FR9: Admin view all detection history records"""
    try:
        history_col = get_detection_history_collection()
        if history_col is None:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        records = [_serialize(doc) for doc in history_col.find().sort('_id', -1)]

        log_admin_action("View Detections", f"Admin accessed {len(records)} detection records")

        return jsonify({
            'success': True,
            'total': len(records),
            'detections': records
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to load detections: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: View Reports (CRUD - Read)
# ========================================
@admin_bp.route('/reports', methods=['GET'])
def get_all_reports():
    """FR9: Admin view all community reports"""
    try:
        reports_col = get_reports_collection()
        if reports_col is None:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        records = [_serialize(doc) for doc in reports_col.find().sort('_id', -1)]

        log_admin_action("View Reports", f"Admin accessed {len(records)} report records")

        return jsonify({
            'success': True,
            'total': len(records),
            'reports': records
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to load reports: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Update Report Status (CRUD - Update)
# ✅ FIX: ab report_id se MongoDB document update hota hai
# (report's own 'id' field se dhundta hai, jaisa detect_routes mein banta hai)
# ========================================
@admin_bp.route('/reports/<report_id>/status', methods=['PUT'])
def update_report_status(report_id):
    """FR9: Admin update report status (pending → reviewed)"""
    try:
        reports_col = get_reports_collection()
        if reports_col is None:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        data = request.get_json()
        new_status = data.get('status', 'reviewed').strip()

        valid_statuses = ['pending', 'reviewed', 'resolved', 'rejected']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {valid_statuses}'
            }), 400

        existing = reports_col.find_one({'id': report_id})
        if not existing:
            return jsonify({'success': False, 'error': 'Report not found'}), 404

        old_status = existing.get('status', 'pending')
        reports_col.update_one({'id': report_id}, {'$set': {'status': new_status}})

        log_admin_action(
            "Update Report",
            f"Report {report_id} status changed: {old_status} → {new_status}"
        )

        return jsonify({
            'success': True,
            'message': f'Report {report_id} status updated to {new_status}',
            'report_id': report_id,
            'new_status': new_status
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to update report {report_id}: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Delete Detection Record (CRUD - Delete)
# ✅ FIX: ab MongoDB _id se delete hota hai, list-index se nahi
# (URL param ka naam "index" hi rakha hai taake frontend na badalna pade,
# lekin ab ye Mongo _id ki string expect karta hai)
# ========================================
@admin_bp.route('/detections/<index>', methods=['DELETE'])
def delete_detection(index):
    """
    FR9: Admin delete a detection record
    FR9 Requirement: Backup before destructive operations
    """
    try:
        history_col = get_detection_history_collection()
        if history_col is None:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        try:
            obj_id = ObjectId(index)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid detection record id'}), 400

        deleted_record = history_col.find_one({'_id': obj_id})
        if not deleted_record:
            return jsonify({'success': False, 'error': 'Detection record not found'}), 404

        history_col.delete_one({'_id': obj_id})
        deleted_record = _serialize(deleted_record)

        log_admin_action(
            "Delete Record",
            f"Admin deleted detection record: {deleted_record.get('type', 'Unknown')} | "
            f"Input: {str(deleted_record.get('input', ''))[:50]}"
        )

        remaining = history_col.count_documents({})

        return jsonify({
            'success': True,
            'message': 'Detection record deleted successfully',
            'deleted_record': deleted_record,
            'remaining': remaining
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to delete detection {index}: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Get Audit Logs
# ========================================
@admin_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """FR9: Get all admin operation audit logs"""
    try:
        logs_col = get_audit_logs_collection()
        if logs_col is None:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        logs = [_serialize(doc) for doc in logs_col.find().sort('_id', -1)]

        return jsonify({
            'success': True,
            'total': len(logs),
            'logs': logs
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: System Health Check
# ========================================
@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """FR9: Admin system health check"""
    try:
        from routes.detect_routes import model, vectorizer

        history_col = get_detection_history_collection()
        reports_col = get_reports_collection()
        feedback_col = get_feedback_collection()
        logs_col = get_audit_logs_collection()

        model_status = 'loaded' if model and vectorizer else 'not_loaded'

        log_admin_action("Health Check", "Admin performed system health check")

        return jsonify({
            'success': True,
            'system_status': 'healthy',
            'model_status': model_status,
            'total_detections': history_col.count_documents({}) if history_col is not None else 0,
            'total_reports': reports_col.count_documents({}) if reports_col is not None else 0,
            'total_feedback': feedback_col.count_documents({}) if feedback_col is not None else 0,
            'total_audit_logs': logs_col.count_documents({}) if logs_col is not None else 0,
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Clear All History (Destructive Operation)
# ========================================
@admin_bp.route('/clear-history', methods=['DELETE'])
def clear_history():
    """FR9: Admin clear all detection history"""
    try:
        history_col = get_detection_history_collection()
        if history_col is None:
            return jsonify({'success': False, 'error': 'Database not connected'}), 500

        count = history_col.count_documents({})

        log_admin_action(
            "Clear History",
            f"Admin cleared all detection history — {count} records removed"
        )

        history_col.delete_many({})

        return jsonify({
            'success': True,
            'message': f'All {count} detection records cleared successfully',
            'records_cleared': count,
            'audit_logged': True
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to clear history: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500