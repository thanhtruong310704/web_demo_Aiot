import datetime
from flask import Blueprint, request, jsonify, session, render_template
from services.firebase_config import db_instance as db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return "Cảnh báo: Bạn không có quyền truy cập trang này!", 403
    return render_template('admin.html')

@admin_bp.route('/api/admin/patients', methods=['GET'])
def get_all_patients():
    try:
        users_data = db.reference('/users').get() or {}
        patients = [{'username': uid, 'name': info.get('name', uid), 'device_id': info.get('device_id', 'Chưa kết nối')} for uid, info in users_data.items()]
        return jsonify({'success': True, 'data': patients})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/api/admin/update_firmware', methods=['POST'])
def admin_update_firmware():
    try:
        data = request.json
        version, url = data.get('version'), data.get('url')

        if not version or not url: return jsonify({'success': False, 'message': 'Vui lòng nhập đủ Link và Version!'})

        db.reference('/admin_config/latest_firmware').set({'version': version, 'url': url, 'updated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        devices = db.reference('/devices').get() or {}
        for dev_id in devices.keys():
            db.reference(f'/devices/{dev_id}').update({'firmware_version_pending': version})

        return jsonify({'success': True, 'message': f'Đã đẩy bản cập nhật {version} đến các thiết bị!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/api/admin/patient_history/<username>', methods=['GET'])
def get_patient_history_admin(username):
    try:
        history_data = db.reference(f'/history/{username}').get() or {}
        history_list = [{'time': v.get('time', ''), 'led_grid': v.get('led_grid', []), 'image_path': v.get('image_path', '')} for k, v in history_data.items()]
        history_list.sort(key=lambda x: x['time'])
        return jsonify({'success': True, 'data': history_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})