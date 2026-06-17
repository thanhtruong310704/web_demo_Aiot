from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify
from config.firebase_config import db_instance as db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Kiểm tra Admin
        admin_data = db.reference(f'/admins/{username}').get()
        if admin_data and admin_data.get('password') == password:
            session.update({'logged_in': True, 'user': username, 'role': 'admin'})
            return redirect(url_for('admin.admin_dashboard'))
            
        # Kiểm tra User
        user_data = db.reference(f'/users/{username}').get()
        if user_data and user_data.get('password') == password:
            session.update({'logged_in': True, 'user': username, 'role': 'user'})
            return redirect(url_for('main.index'))
        else:
            error = 'Sai tên đăng nhập hoặc mật khẩu!'
            
    return render_template('login.html', error=error)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_ref = db.reference(f'/users/{username}')
        
        if user_ref.get():
            error = 'Tên tài khoản này đã có người sử dụng! Vui lòng chọn tên khác.'
        else:
            user_ref.set({'password': password, 'name': username, 'auth_provider': 'local'})
            return redirect(url_for('auth.login'))
            
    return render_template('register.html', error=error)

@auth_bp.route('/oauth_login', methods=['POST'])
def oauth_login():
    try:
        data = request.json
        uid, email, name = data.get('uid'), data.get('email'), data.get('displayName')
        if not uid: 
            return jsonify({"success": False, "message": "Dữ liệu xác thực không hợp lệ!"}), 400
            
        user_ref = db.reference(f'/users/{uid}')
        if not user_ref.get():
            user_ref.set({'email': email, 'name': name, 'auth_provider': 'google'})
            
        session.update({'logged_in': True, 'user': uid, 'role': 'user'})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))