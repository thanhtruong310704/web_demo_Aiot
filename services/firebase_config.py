import os
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Nạp các biến môi trường từ file .env
load_dotenv()

def init_firebase():
    """Khởi tạo kết nối Firebase bằng Singleton Pattern"""
    if not firebase_admin._apps:
        # Sử dụng service account key để định danh quyền Admin Backend
        cred = credentials.Certificate("config/serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv("databaseURL")
        })
    return db

db_instance = init_firebase()