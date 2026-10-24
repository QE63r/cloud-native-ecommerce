from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = './data/product.db'

def init_db():
    os.makedirs('./data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  price REAL NOT NULL,
                  stock INTEGER NOT NULL DEFAULT 0,
                  description TEXT,
                  image TEXT)''')
    try:
        products = [
            ("云服务器 ECS", 99.0, 100, "高性能云计算服务器，弹性扩展", "/assets/images/1.jpg"),
            ("对象存储 OSS", 19.9, 500, "海量安全的云存储服务", "/assets/images/2.jpg"),
            ("云数据库 RDS", 159.0, 50, "高可用关系型数据库服务", "/assets/images/3.jpg"),
            ("CDN 加速", 29.9, 200, "全球节点内容分发加速", "/assets/images/4.jpg"),
            ("容器服务 K8s", 299.0, 30, "企业级容器编排引擎", "/assets/images/5.jpg"),
            ("云安全中心", 89.0, 80, "全方位云安全防护服务", "/assets/images/6.jpg")
        ]
        c.executemany("INSERT INTO products (name, price, stock, description, image) VALUES (?,?,?,?,?)", products)
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

@app.route('/api/product/list', methods=['GET'])
def product_list():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 10))
    offset = (page - 1) * size
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, price, stock, image FROM products LIMIT ? OFFSET ?", (size, offset))
    rows = c.fetchall()
    c.execute("SELECT count(*) FROM products")
    total = c.fetchone()[0]
    conn.close()
    
    list_data = [
        {"id": r[0], "name": r[1], "price": r[2], "stock": r[3], "image": r[4]}
        for r in rows
    ]
    return success({"list": list_data, "total": total, "page": page, "size": size})

@app.route('/api/product/info/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, price, stock, description, image FROM products WHERE id = ?", (product_id,))
    p = c.fetchone()
    conn.close()
    if p:
        return success({
            "id": p[0], "name": p[1], "price": p[2],
            "stock": p[3], "description": p[4], "image": p[5]
        })
    return error("商品不存在", 404)

@app.route('/api/product/deduct', methods=['POST'])
def deduct_stock():
    data = request.get_json()
    product_id = data.get('product_id')
    num = data.get('num', 1)
    if not product_id or num <= 0:
        return error("参数错误")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    stock = c.fetchone()
    if not stock:
        conn.close()
        return error("商品不存在", 404)
    if stock[0] < num:
        conn.close()
        return error("库存不足")
    
    c.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (num, product_id, num))
    if c.rowcount == 0:
        conn.rollback()
        conn.close()
        return error("库存不足")
    conn.commit()
    conn.close()
    return success()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8002)
