import os
import json
import random
import datetime
import paho.mqtt.client as mqtt
# Import trực tiếp instance db mà ta vừa tạo ở trên
from config.firebase_config import db_instance as db

def on_mqtt_message(client, userdata, msg):
    """
    Callback: Lắng nghe và xử lý dữ liệu từ Mặt nạ gửi lên (ví dụ: % Pin)
    Luồng dữ liệu: Phần cứng -> MQTT Broker -> Python -> Firebase DB
    """
    if "battery" in msg.topic:
        try:
            # Parse MAC Address từ topic: devices/AA:BB:CC/battery
            mac_address = msg.topic.split('/')[1]
            battery_level = msg.payload.decode('utf-8')
            
            # Cập nhật trực tiếp lên DB để Web Frontend có thể đọc được
            db.reference(f'/devices/{mac_address}').update({'battery': battery_level})
        except Exception as e:
            print("Lỗi nhận MQTT:", e)

def setup_mqtt_client():
    """Khởi tạo và cấu hình luồng chạy ngầm cho MQTT"""
    client = mqtt.Client(
        client_id=f"Web_Backend_{random.randint(10000, 99999)}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        clean_session=True
    )
    client.on_message = on_mqtt_message
    client.username_pw_set(os.getenv("MQTT_USER"), os.getenv("MQTT_PASSWORD"))
    client.tls_set() # Bắt buộc để kết nối mã hóa SSL/TLS
    client.connect(os.getenv("MQTT_SERVER"), int(os.getenv("MQTT_PORT")), keepalive=60)
    
    # Subscribe nhận thông tin từ toàn bộ thiết bị (dấu + là wildcard)
    client.subscribe("devices/+/battery")
    client.loop_start() # Chạy ngầm không chặn luồng (non-blocking)
    return client

# Khởi tạo Client
mqtt_client = setup_mqtt_client()

def send_control_command(device_id, led_grid, bright_grid, user_id):
    """
    Hàm Helper: Đồng bộ lệnh điều khiển xuống cả Phần cứng và Database
    """
    checksum = sum(led_grid) + sum(bright_grid)
    
    # 1. Bắn lệnh xuống thiết bị qua MQTT
    payload = {"led_grid": led_grid, "bright_grid": bright_grid}
    mqtt_client.publish(f"devices/{device_id}/control", json.dumps(payload))
    
    # 2. Cập nhật trạng thái "đang sáng" lên Firebase
    db.reference(f'/devices/{device_id}').update({
        'led_grid': led_grid,
        'bright_grid': bright_grid,
        'checksum': checksum,
        'last_user': user_id,
        'last_update': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })