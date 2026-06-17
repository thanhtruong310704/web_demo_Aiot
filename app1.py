import os
from flask import Flask
from dotenv import load_dotenv
from waitress import serve
from pyngrok import ngrok
import config.firebase_config
import services.mqtt_service
from routes.auth import auth_bp
from routes.device import device_bp
from routes.processing import processing_bp
from routes.admin import admin_bp
from routes.user_data import user_data_bp
from routes.home import main_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = 'bi mat bat mi'

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