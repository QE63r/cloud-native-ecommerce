from flask import Flask, request, jsonify
import sqlite3
import os
import requests

app = Flask(__name__)
DB_PATH = './data/order.db'

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://127.0.0.1:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8002")

def init_db():
    os.makedirs('./data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  product_id INTEGER NOT NULL,
                  product_name TEXT NOT NULL,
                  num INTEGER NOT NULL,
                  total_price REAL NOT NULL,
                  status TEXT DEFAULT 'created',
                  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def success(data=None):
    return jsonify({"code": 0, "msg": "success", "data": data})

def error(msg, code=400):
    return jsonify({"code": code, "msg": msg}), code

@app.route('/health')
def health():
    return success({"status": "ok"})

@app.route('/api/order/create', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    num = data.get('num', 1)
    
    if not user_id or not product_id:
        return error("参数不全")
    if num <= 0:
        return error("数量必须大于0")

    try:
        res = requests.get(f"{USER_SERVICE_URL}/api/user/info/{user_id}", timeout=3)
        user_res = res.json()
        if user_res['code'] != 0:
            return error("用户不存在")
    except Exception:
        return error("用户服务暂不可用", 503)

    try:
        res = requests.post(f"{PRODUCT_SERVICE_URL}/api/product/deduct",
                            json={"product_id": product_id, "num": num}, timeout=3)
        stock_res = res.json()
        if stock_res['code'] != 0:
            return error(stock_res['msg'])
    except Exception:
        return error("商品服务暂不可用", 503)

    res = requests.get(f"{PRODUCT_SERVICE_URL}/api/product/info/{product_id}", timeout=3)
    product = res.json()['data']
    total_price = product['price'] * num

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, product_id, product_name, num, total_price) VALUES (?,?,?,?,?)",
              (user_id, product_id, product['name'], num, total_price))
    order_id = c.lastrowid
    conn.commit()
    conn.close()

    return success({"order_id": order_id, "total_price": total_price})

@app.route('/api/order/list/<int:user_id>', methods=['GET'])
def order_list(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, product_name, num, total_price, status, create_time FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
    orders = c.fetchall()
    conn.close()
    
    list_data = [
        {"id": o[0], "product_name": o[1], "num": o[2],
         "total_price": o[3], "status": o[4], "create_time": o[5]}
        for o in orders
    ]
    return success(list_data)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8003)
