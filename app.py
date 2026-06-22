import os                                                                                                                                                                                     # Author: Thanh Trường
import logging
from flask import Flask, request, session 
from dotenv import load_dotenv
from waitress import serve
from pyngrok import ngrok
import services.firebase_config
import services.mqtt_service
from routes.auth import auth_bp
from routes.device import device_bp
from routes.processing import processing_bp
from routes.admin import admin_bp
from routes.user_data import user_data_bp
from routes.main import main_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = 'Thanh Truong'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

@app.after_request
def log_request(response):
    """in ra mọi request đi qua server"""
    current_user = session.get('user', 'Khách')
    print(f"User: {current_user} | {request.method} {request.path} - Mã trạng thái: {response.status_code}")
    return response

app.register_blueprint(auth_bp)
app.register_blueprint(device_bp)
app.register_blueprint(processing_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_data_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        try:
            ngrok.set_auth_token(os.getenv("PYNGOK_TOKEN"))
            public_url = ngrok.connect(5000).public_url
            print(f"[*] Ngrok tunnel đã mở tại: {public_url}")
        except Exception as e:
            print(f"[!] Không thể khởi tạo Ngrok: {e}")
            
    print("[*] Server đang khởi động với Waitress WSGI...")
    serve(app, host='0.0.0.0', port=5000, threads=4)