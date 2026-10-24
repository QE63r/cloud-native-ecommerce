from flask import Flask, request, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DB_PATH = './data/user.db'

def init_db():
    os.makedirs('./data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    try:
        password_hash = generate_password_hash('123456')
        c.execute("INSERT INTO users (username, password) VALUES ('test', ?)", (password_hash,))
    except:
        pass
    conn.commit()
    conn.close()

def success(data=None):
    return jsonify({"code": 0, "msg": "success", "data": data})

def error(msg, code=400):
    return jsonify({"code": code, "msg": msg}), code

@app.route('/health')
def health():
    return success({"status": "ok"})

@app.route('/api/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return error("用户名和密码不能为空")
    if len(username) < 3 or len(password) < 6:
        return error("用户名至少3位，密码至少6位")
    
    try:
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return success({"username": username})
    except sqlite3.IntegrityError:
        return error("用户名已存在")

@app.route('/api/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    if not username or not password:
        return error("用户名和密码不能为空")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        return success({"id": user[0], "username": user[1]})
    return error("用户名或密码错误", 401)

@app.route('/api/user/info/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, create_time FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return success({"id": user[0], "username": user[1], "create_time": user[2]})
    return error("用户不存在", 404)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8001)
