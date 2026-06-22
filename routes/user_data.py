import os
from flask import Blueprint, jsonify, session, send_file, request
from services.firebase_config import db_instance as db

user_data_bp = Blueprint('user_data', __name__)

@user_data_bp.route('/get_history', methods=['GET'])
def get_history():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
    try:
        user = session.get('user')
        history_data = db.reference(f'/history/{user}').get()
        history_list = []
        if history_data:
            for key, value in history_data.items():
                history_list.append({
                    'time': value.get('time', ''),
                    'led_grid': value.get('led_grid', []),
                    'image_path': value.get('image_path', '')
                })
            history_list.sort(key=lambda x: x['time'], reverse=True)
        return jsonify({"success": True, "data": history_list})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@user_data_bp.route('/api/image', methods=['GET'])
def get_image():
    if not session.get('logged_in'): return "Chưa đăng nhập", 401
    filepath = request.args.get('path')
    
    if filepath and os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    return "Không tìm thấy ảnh", 404