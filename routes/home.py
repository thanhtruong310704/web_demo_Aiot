from flask import Blueprint, render_template, session, redirect, url_for
from services.firebase_config import db_instance as db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user')
    user_data = db.reference(f'/users/{user_id}').get()
    device_id = user_data.get('device_id') if user_data else None
    display_name = user_data.get('name', user_id) if user_data else 'Khách'
    
    return render_template('index.html', username=display_name, device_id=device_id)