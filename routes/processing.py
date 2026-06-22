import os
import datetime
import base64
from flask import Blueprint, request, jsonify, session
from services.firebase_config import db_instance as db
from services.mqtt_service import send_control_command
from services.image_service import FaceAnalyzerService

processing_bp = Blueprint('processing', __name__)
ai_service = FaceAnalyzerService(model_path='/content/drive/MyDrive/web_unet/models/unet_final.keras')

@processing_bp.route('/process_image', methods=['POST'])
def process_image():
    if not session.get('logged_in'): 
        return jsonify({"success": False, "message": "Chưa đăng nhập!"}), 401
        
    try:
        user = session.get('user')
        base64_image = request.json.get('image')
        
        # 1. Gọi Service xử lý ảnh AI độc lập
        is_success, result_data, error_msg = ai_service.process_image(base64_image)
        if not is_success: 
            return jsonify({"success": False, "message": error_msg})
            
        user_data = db.reference(f'/users/{user}').get()
        device_id = user_data.get('device_id') if user_data else None

        if not device_id: 
            return jsonify({"success": False, "message": "Bạn chưa kết nối với mặt nạ nào!"})

        led_grid = result_data['led_grid']
        bright_grid = result_data['bright_grid']
        checksum = sum(led_grid) + sum(bright_grid)
        
        # 2. LƯU FILE VẬT LÝ
        try:
            save_dir = '/content/drive/MyDrive/web_unet/static/images'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"{save_dir}/{user}_{timestamp}.png"
            file_path_resized = f"{save_dir}/{user}_{timestamp}_resized.png"
            
            img_b64_data = result_data['image'].split(',')[1]
            with open(file_path, "wb") as fh:
                fh.write(base64.b64decode(img_b64_data))
                
            if 'image_resized' in result_data:
                img_resized_b64_data = result_data['image_resized'].split(',')[1]
                with open(file_path_resized, "wb") as fh:
                    fh.write(base64.b64decode(img_resized_b64_data))
                    
        except Exception as ex:
            print(f"Lỗi lưu ảnh: {str(ex)}")
            file_path = "Không thể lưu ảnh"

        # 3. GIAO TIẾP VỚI PHẦN CỨNG (MQTT & FIREBASE)
        send_control_command(device_id, led_grid, bright_grid, user)
        
        ref_device = db.reference(f'/devices/{device_id}')
        ref_device.update({
            'led_grid': led_grid,
            'bright_grid': bright_grid,
            'checksum': checksum,
            'last_user': user,
            'last_update': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        db.reference(f'/history/{user}').push({
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'led_grid': led_grid,
            'image_path': file_path
        })

        if 'image_resized' in result_data:
            del result_data['image_resized']

        result_data['success'] = True
        return jsonify(result_data)

    except Exception as e:
        print(f"Lỗi hệ thống: {str(e)}")
        return jsonify({"success": False, "message": str(e)})