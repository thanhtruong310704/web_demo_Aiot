import json
import datetime
from flask import Blueprint, request, jsonify, session
from config.firebase_config import db_instance as db
from services.mqtt_service import mqtt_client, send_control_command

device_bp = Blueprint('device', __name__)

@device_bp.route('/bind_device', methods=['POST'])
def bind_device():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
    try:
        data, username = request.json, session.get('user')
        device_id, pin = data.get('device_id'), data.get('pin')
        
        device_ref = db.reference(f'/devices/{device_id}')
        device_data = device_ref.get()
        
        if device_data and str(device_data.get('pin')) == str(pin):
            if device_data.get('owner') and device_data.get('owner') != username:
                return jsonify({"success": False, "message": "Thiết bị này đã có người sở hữu!"})
            
            device_ref.update({'owner': username})
            db.reference(f'/users/{username}').update({'device_id': device_id})
            return jsonify({"success": True, "message": "Kết nối mặt nạ thành công!"})
        return jsonify({"success": False, "message": "Mã thiết bị hoặc PIN không chính xác!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@device_bp.route('/unbind_device', methods=['POST'])
def unbind_device():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
    try:
        username = session.get('user')
        user_ref = db.reference(f'/users/{username}')
        device_id = user_ref.get().get('device_id') if user_ref.get() else None
        
        if device_id:
            db.reference(f'/devices/{device_id}/owner').delete()
            user_ref.child('device_id').delete()
            return jsonify({"success": True, "message": "Đã ngắt kết nối thiết bị!"})
        return jsonify({"success": False, "message": "Bạn chưa kết nối thiết bị nào."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@device_bp.route('/update_leds', methods=['POST'])
def update_leds():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
    try:
        data, user = request.json, session.get('user')
        led_grid, bright_grid = data.get('grid', []), data.get('bright', [])
        bright_grid = [min(b, 25) for b in bright_grid] # An toàn PWM
        
        device_id = db.reference(f'/users/{user}').get().get('device_id')
        if not device_id: return jsonify({"success": False, "message": "Bạn chưa kết nối với chiếc mặt nạ nào!"})

        send_control_command(device_id, led_grid, bright_grid, user)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@device_bp.route('/trigger_ota', methods=['POST'])
def trigger_ota():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
    try:
        user = session.get('user')
        device_id = db.reference(f'/users/{user}').get().get('device_id')
        if not device_id: return jsonify({"success": False, "message": "Bạn chưa kết nối mặt nạ!"})

        admin_config = db.reference('/admin_config/latest_firmware').get()
        if not admin_config or not admin_config.get('url'):
            return jsonify({"success": False, "message": "Hệ thống chưa có bản cập nhật nào!"})

        latest_url, pending_version = admin_config.get('url'), admin_config.get('version', '--')
        time_stamp = datetime.datetime.now().strftime("%H%M%S")
        forced_url = f"{latest_url}&t={time_stamp}" if "?" in latest_url else f"{latest_url}?t={time_stamp}"

        mqtt_client.publish(f"devices/{device_id}/control", json.dumps({"start_ota_now": True, "ota_url": forced_url}), retain=True)

        db.reference(f'/devices/{device_id}').update({
            'firmware_version_pending': pending_version,
            'last_user': user,
            'last_update': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return jsonify({"success": True, "message": "Đã ra lệnh cập nhật! Mặt nạ đang tải phần mềm..."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@device_bp.route('/get_device_stats', methods=['GET'])
def get_device_stats():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    user_id = session.get('user')
    device_id = db.reference(f'/users/{user_id}').get().get('device_id')
    if not device_id: return jsonify({"success": False, "message": "Chưa kết nối thiết bị"})

    device_data = db.reference(f'/devices/{device_id}').get()
    battery, firmware, last_used, pending_version = "--", "--", "--", None

    if isinstance(device_data, dict):
        battery, firmware = device_data.get('battery', "--"), device_data.get('firmware_version', "--")
        pending_version = device_data.get('firmware_version_pending')

        last_update_str = device_data.get('last_update')
        if last_update_str:
            try:
                last_time = datetime.datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
                diff = int((datetime.datetime.now() - last_time).total_seconds() / 60)
                if diff < 1: last_used = "Vừa xong"
                elif diff < 60: last_used = f"{diff} Phút"
                elif diff < 1440: last_used = f"{diff // 60} Giờ"
                else: last_used = f"{diff // 1440} Ngày"
            except: last_used = "Đang cập nhật"

    return jsonify({"success": True, "battery": battery, "firmware": firmware, "pending_version": pending_version, "last_used": last_used, "device_id": device_id})