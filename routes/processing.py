import os
import datetime
from flask import Blueprint, request, jsonify, session
from services.firebase_config import db_instance as db
from services.mqtt_service import send_control_command
from services.image_service import FaceAnalyzerService

processing_bp = Blueprint('processing', __name__)
# Khởi tạo instance AI. Trong thực tế, bạn nên cấu hình đường dẫn qua .env
ai_service = FaceAnalyzerService(model_path='/content/drive/MyDrive/web_unet/models/unet_final.keras')

@processing_bp.route('/process_image', methods=['POST'])
def process_image():
    if not session.get('logged_in'): return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
        
    try:
        user = session.get('user')
        base64_image = request.json.get('image')
        
        # Gọi Service xử lý ảnh đã tách ra
        is_success, result_data, error_msg = ai_service.process_image(base64_image)
        if not is_success: return jsonify({"success": False, "message": error_msg})
            
        device_id = db.reference(f'/users/{user}').get().get('device_id')
        if not device_id: return jsonify({"success": False, "message": "Bạn chưa kết nối với mặt nạ nào!"})

        send_control_command(device_id, result_data['led_grid'], result_data['bright_grid'], user)
        
        # Lưu file vật lý (Dựa trên logic gốc)
        save_dir = '/content/drive/MyDrive/web_unet/static/images'
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"{save_dir}/{user}_{timestamp}.png"
        
        # Ở đây tôi giả định bạn đã sửa service để trả ra ảnh cv2 thô trong result_data['raw_cv2_image']
        # cv2.imwrite(file_path, result_data['raw_cv2_image'])
        # Tạm lưu đường dẫn ảo theo cấu trúc cũ:
        file_path = f"{save_dir}/{user}_{timestamp}.png"

        # Lưu lịch sử Firebase
        db.reference(f'/history/{user}').push({
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'led_grid': result_data['led_grid'],
            'image_path': file_path
        })

        return jsonify(result_data)

    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi Server: {str(e)}"}), 500