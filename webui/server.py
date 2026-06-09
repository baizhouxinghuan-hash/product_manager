import os
import random
import string
import threading
from datetime import timedelta
from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
from astrbot.api import logger

# ======================
# 全局变量
# ======================
_product_store = None  # 由 main.py 注入

BASE_DIR = os.path.dirname(__file__)
IMAGE_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
PASSWORD_FILE = os.path.join(BASE_DIR, 'webui_pass.txt')
WEBUI_PORT = 5465

# 允许上传的图片扩展名
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

os.makedirs(IMAGE_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
# Session 过期时间（2小时）
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
WEBUI_PASSWORD = None

# ======================
# 启动 WebUI（线程方式，不阻塞主进程）
# ======================
def run_webui(product_store):
    global _product_store
    _product_store = product_store

    _init_password()
    logger.info(f"[WebUI] 商品后台已启动：http://127.0.0.1:{WEBUI_PORT}")

    # 使用 Waitress 生产级服务器
    from waitress import serve
    threading.Thread(
        target=lambda: serve(app, host='0.0.0.0', port=WEBUI_PORT, threads=4),
        daemon=True
    ).start()

# ======================
# 密码初始化（默认 moren）
# ======================
def _init_password():
    global WEBUI_PASSWORD
    if not os.path.exists(PASSWORD_FILE):
        WEBUI_PASSWORD = "moren"
        with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
            f.write(WEBUI_PASSWORD)
        logger.info(f"[WebUI] 默认密码已设置为：{WEBUI_PASSWORD}")
    else:
        with open(PASSWORD_FILE, 'r', encoding='utf-8') as f:
            WEBUI_PASSWORD = f.read().strip()

# ======================
# 路由：登录
# ======================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == WEBUI_PASSWORD:
            session['login'] = True
            session.permanent = True  # 启用 session 过期
            return redirect(url_for('index'))
        return render_template('login.html', error='密码错误')
    return render_template('login.html')

# ======================
# 路由：首页（商品列表）
# ======================
@app.route('/index')
def index():
    if not session.get('login'):
        return redirect(url_for('login'))
    products = _product_store.get_all_products()
    return render_template('index.html', products=products)

# ======================
# 路由：添加商品表单页面
# ======================
@app.route('/add_page')
def add_product_page():
    if not session.get('login'):
        return redirect(url_for('login'))
    return render_template('add_product.html')

# ======================
# 路由：提交添加商品
# ======================
@app.route('/add', methods=['POST'])
def add_product():
    if not session.get('login'):
        return redirect(url_for('login'))

    name = request.form.get('name') or '未知'
    description = request.form.get('description') or '未知'
    try:
        price = float(request.form.get('price') or 0.0)
    except (ValueError, TypeError):
        price = 0.0

    image = request.files.get('image')
    image_name = None
    if image and image.filename:
        # 校验文件扩展名
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return render_template('add_product.html', error='不支持的图片格式，仅支持：jpg, jpeg, png, gif, webp, bmp')
        image_name = f"{random.randint(1, 99999999)}_{image.filename}"
        image.save(os.path.join(IMAGE_FOLDER, image_name))

    # ✅ 使用 add_product 并统一字段名 allow_auto_inject
    _product_store.add_product({
        "name": name,
        "description": description,
        "price": price,
        "image": image_name,
        "importance": 0.9,
        "active": True,
        "allow_auto_inject": True,
        "aliases": []
    })

    return redirect(url_for('index'))

# ======================
# 路由：切换上下架
# ======================
@app.route('/toggle/<int:product_id>')
def toggle_product(product_id):
    if not session.get('login'):
        return redirect(url_for('login'))
    _product_store.toggle_active(product_id)
    return redirect(url_for('index'))

# ======================
# 路由：删除商品
# ======================
@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    if not session.get('login'):
        return redirect(url_for('login'))
    _product_store.delete(product_id)
    return redirect(url_for('index'))

# ======================
# 路由：显示图片
# ======================
@app.route('/images/<filename>')
def images(filename):
    # 防止路径穿越攻击
    if '..' in filename or '/' in filename or '\\' in filename:
        return "Invalid path", 400
    return send_from_directory(IMAGE_FOLDER, filename)

# ======================
# 路由：修改密码
# ======================
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    global WEBUI_PASSWORD
    if not session.get('login'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_pass = request.form.get('new_password')
        if new_pass:
            WEBUI_PASSWORD = new_pass
            with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
                f.write(WEBUI_PASSWORD)
            return render_template('change_password.html', success=True)
    return render_template('change_password.html', success=False)
