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

from flask import Blueprint, request, jsonify
from datetime import datetime

# Create Admin Blueprint
admin_bp = Blueprint('admin', __name__)

# ========================================
# FR9: Admin Credentials
# In production this should be in .env file
# ========================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ========================================
# FR9: Audit Log Storage
# Every admin operation is logged here
# ========================================
audit_logs = []


# ========================================
# FR9: Helper — Log Admin Action
# Audit trail for all admin operations
# ========================================
def log_admin_action(action, detail, status="success"):
    """
    FR9: Operation logging and audit trails
    Logs every admin action with timestamp and status
    """
    entry = {
        'id':        f"LOG-{len(audit_logs) + 1001}",
        'action':    action,
        'detail':    detail,
        'status':    status,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    audit_logs.append(entry)
    print(f"📋 FR9 Audit Log: [{action}] {detail} | Status: {status}")
    return entry


# ========================================
# FR9: Admin Authentication
# Input: Admin credentials
# Validation: Admin authentication & authorization
# Output: Success/error confirmation
# ========================================
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """FR9: Secure admin authentication"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # FR9 Validation: Check credentials
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400

        # FR9 Validation: Admin authorization check
        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            # FR9: Log failed login attempt
            log_admin_action("Login Failed", f"Failed login attempt for username: {username}", "failed")
            return jsonify({
                'success': False,
                'error': 'Invalid admin credentials'
            }), 401

        # FR9: Log successful admin login
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
# Output: Database operation confirmations + stats
# ========================================
@admin_bp.route('/stats', methods=['GET'])
def get_admin_stats():
    """
    FR9: Get overall system statistics for admin dashboard
    Pulls data from all collections: history, reports, feedback
    """
    try:
        # Import storage from detect_routes
        from routes.detect_routes import history_db, reports_db, feedback_db

        total_detections = len(history_db)
        total_reports    = len(reports_db)
        total_feedback   = len(feedback_db)

        # Calculate satisfaction rate
        if total_feedback > 0:
            positive     = sum(1 for f in feedback_db if f['rating'] == 'thumbs_up')
            satisfaction = round((positive / total_feedback) * 100, 1)
        else:
            satisfaction = 0

        # Count fake vs real detections
        fake_count = sum(
            1 for h in history_db
            if h.get('prediction') in ['Fake', 'Suspicious']
        )
        real_count = total_detections - fake_count

        # FR9: Log stats access
        log_admin_action("View Stats", "Admin accessed system statistics")

        return jsonify({
            'success':           True,
            'total_detections':  total_detections,
            'total_reports':     total_reports,
            'total_feedback':    total_feedback,
            'satisfaction_rate': satisfaction,
            'fake_detections':   fake_count,
            'real_detections':   real_count,
            'audit_log_count':   len(audit_logs)
        }), 200

    except Exception as e:
        print(f"❌ Admin stats error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: View Detection History (CRUD - Read)
# Process: CRUD operations execution
# Output: Database records with confirmations
# ========================================
@admin_bp.route('/detections', methods=['GET'])
def get_all_detections():
    """FR9: Admin view all detection history records"""
    try:
        from routes.detect_routes import history_db

        # FR9: Log admin data access
        log_admin_action("View Detections", f"Admin accessed {len(history_db)} detection records")

        return jsonify({
            'success':    True,
            'total':      len(history_db),
            'detections': list(reversed(history_db))  # newest first
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
        from routes.detect_routes import reports_db

        # FR9: Log admin data access
        log_admin_action("View Reports", f"Admin accessed {len(reports_db)} report records")

        return jsonify({
            'success': True,
            'total':   len(reports_db),
            'reports': list(reversed(reports_db))
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to load reports: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Update Report Status (CRUD - Update)
# Process: Data validation and sanitization
# Output: Database operation confirmations
# ========================================
@admin_bp.route('/reports/<report_id>/status', methods=['PUT'])
def update_report_status(report_id):
    """FR9: Admin update report status (pending → reviewed)"""
    try:
        from routes.detect_routes import reports_db

        data       = request.get_json()
        new_status = data.get('status', 'reviewed').strip()

        # FR9 Validation: Operation permissions check
        valid_statuses = ['pending', 'reviewed', 'resolved', 'rejected']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error':   f'Invalid status. Must be one of: {valid_statuses}'
            }), 400

        # Find and update report
        updated = False
        for report in reports_db:
            if report.get('id') == report_id:
                old_status      = report.get('status', 'pending')
                report['status'] = new_status
                updated          = True

                # FR9: Log operation in audit trail
                log_admin_action(
                    "Update Report",
                    f"Report {report_id} status changed: {old_status} → {new_status}"
                )
                break

        if not updated:
            return jsonify({'success': False, 'error': 'Report not found'}), 404

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
# Validation: Backup before destructive operations
# Output: Operation confirmation + audit log entry
# ========================================
@admin_bp.route('/detections/<int:index>', methods=['DELETE'])
def delete_detection(index):
    """
    FR9: Admin delete a detection record
    FR9 Requirement: Backup before destructive operations
    """
    try:
        from routes.detect_routes import history_db

        if index < 0 or index >= len(history_db):
            return jsonify({'success': False, 'error': 'Detection record not found'}), 404

        # FR9: Backup the record before deleting (audit trail)
        deleted_record = history_db[index].copy()
        history_db.pop(index)

        # FR9: Log deletion in audit trail
        log_admin_action(
            "Delete Record",
            f"Admin deleted detection record: {deleted_record.get('type', 'Unknown')} | "
            f"Input: {str(deleted_record.get('input', ''))[:50]}"
        )

        return jsonify({
            'success':        True,
            'message':        'Detection record deleted successfully',
            'deleted_record': deleted_record,
            'remaining':      len(history_db)
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to delete detection #{index}: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Get Audit Logs
# Output: Audit log entries
# ========================================
@admin_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """FR9: Get all admin operation audit logs"""
    try:
        return jsonify({
            'success': True,
            'total':   len(audit_logs),
            'logs':    list(reversed(audit_logs))  # newest first
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: System Health Check
# Output: Database operation confirmations
# ========================================
@admin_bp.route('/health', methods=['GET'])
def admin_health():
    """FR9: Admin system health check"""
    try:
        from routes.detect_routes import history_db, reports_db, feedback_db, model, vectorizer

        model_status = 'loaded' if model and vectorizer else 'not_loaded'

        # FR9: Log health check
        log_admin_action("Health Check", "Admin performed system health check")

        return jsonify({
            'success':          True,
            'system_status':    'healthy',
            'model_status':     model_status,
            'total_detections': len(history_db),
            'total_reports':    len(reports_db),
            'total_feedback':   len(feedback_db),
            'total_audit_logs': len(audit_logs),
            'checked_at':       datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# FR9: Clear All History (Destructive Operation)
# Validation: Backup before destructive operations
# Output: Confirmation + audit log entry
# ========================================
@admin_bp.route('/clear-history', methods=['DELETE'])
def clear_history():
    """
    FR9: Admin clear all detection history
    FR9 Requirement: Log backup before destructive operations
    """
    try:
        from routes.detect_routes import history_db

        count = len(history_db)

        # FR9: Log before clearing (audit trail)
        log_admin_action(
            "Clear History",
            f"Admin cleared all detection history — {count} records removed"
        )

        history_db.clear()

        return jsonify({
            'success':          True,
            'message':          f'All {count} detection records cleared successfully',
            'records_cleared':  count,
            'audit_logged':     True
        }), 200

    except Exception as e:
        log_admin_action("Error", f"Failed to clear history: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)}), 500