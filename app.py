from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import time
import json
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# مسارات الملفات
USERS_FILE = 'data/users.txt'
MESSAGES_FILE = 'data/messages.txt'

# التأكد من وجود ملفات البيانات
def ensure_data_files_exist():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            f.write('')
    
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            f.write('')

# تشفير كلمة المرور
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# التحقق من وجود المستخدم
def user_exists(username):
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                user_data = json.loads(line)
                if user_data['username'] == username:
                    return True
    return False

# إضافة مستخدم جديد
def add_user(username, password):
    hashed_password = hash_password(password)
    user_data = {
        'username': username,
        'password': hashed_password,
        'created_at': int(time.time())
    }
    
    with open(USERS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(user_data) + '\n')
    
    return True

# التحقق من صحة بيانات تسجيل الدخول
def verify_login(username, password):
    hashed_password = hash_password(password)
    
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                user_data = json.loads(line)
                if user_data['username'] == username and user_data['password'] == hashed_password:
                    return True
    
    return False

# إضافة رسالة جديدة
def add_message(username, text):
    message_id = int(time.time() * 1000)  # استخدام الوقت كمعرف فريد
    message_data = {
        'id': message_id,
        'username': username,
        'text': text,
        'timestamp': int(time.time())
    }
    
    with open(MESSAGES_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(message_data) + '\n')
    
    return message_id

# الحصول على الرسائل منذ وقت معين
def get_messages(since_time=0):
    messages = []
    
    with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                message_data = json.loads(line)
                if message_data['timestamp'] > since_time:
                    messages.append(message_data)
    
    return sorted(messages, key=lambda x: x['timestamp'])

# التأكد من وجود ملفات البيانات عند بدء التطبيق
ensure_data_files_exist()

# الصفحة الرئيسية
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        if verify_login(username, password):
            session['username'] = username
            if request.is_json:
                return jsonify({'success': True})
            return redirect(url_for('chat'))
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'})
    
    return render_template('login.html')

# صفحة التسجيل
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        if user_exists(username):
            if request.is_json:
                return jsonify({'success': False, 'message': 'اسم المستخدم موجود بالفعل'})
        
        add_user(username, password)
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('login'))
    
    return render_template('register.html')

# صفحة الدردشة
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('chat.html')

# التحقق من تسجيل الدخول
@app.route('/check-auth')
def check_auth():
    if 'username' in session:
        return jsonify({'authenticated': True, 'username': session['username']})
    return jsonify({'authenticated': False})

# الحصول على الرسائل
@app.route('/messages')
def messages():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    since = request.args.get('since', 0, type=int)
    messages_list = get_messages(since)
    
    return jsonify({'success': True, 'messages': messages_list})

# إرسال رسالة
@app.route('/send-message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'غير مصرح'})
    
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'success': False, 'message': 'الرسالة فارغة'})
    
    message_id = add_message(session['username'], text)
    
    return jsonify({'success': True, 'message_id': message_id})

# تسجيل الخروج
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

if __name__ == '__main__':
    # للتشغيل المحلي
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # للتشغيل على منصات الاستضافة مثل Railway
    # تأكد من أن ملفات البيانات موجودة
    ensure_data_files_exist()
