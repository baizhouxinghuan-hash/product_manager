import os
import json
import threading

class ProductStore:
    def __init__(self, product_file: str = None):
        """
        商品存储管理
        - product_file: products.json 路径（可选）
        """
        if product_file is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            product_file = os.path.join(base_dir, 'products.json')

        self.product_file = product_file
        self._lock = threading.Lock()

        # 如果文件不存在，初始化为空列表
        if not os.path.exists(self.product_file):
            with open(self.product_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    # ========= 基础读写 =========
    def _load(self):
        with self._lock:
            with open(self.product_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _save(self, products):
        with self._lock:
            with open(self.product_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)

    # ========= CRUD =========
    def get_all(self):
        return self._load()

    def add_product(self, product: dict):
        products = self._load()
        product['id'] = len(products)

        # 默认字段处理
        product.setdefault('active', True)
        product.setdefault('allow_auto_inject', True)  # 统一字段
        product.setdefault('aliases', [])
        product.setdefault('importance', {"name":0.9, "description":0.7, "price":0.9})
        product.setdefault('status', 'on_shelf' if product.get('active', True) else 'off_shelf')

        products.append(product)
        self._save(products)

    # 兼容 server.py 的 add()
    def add(self, product: dict):
        self.add_product(product)

    def delete(self, product_id: int):
        products = self._load()
        products = [p for p in products if p.get('id') != product_id]

        # 重新编号 ID 保持连续
        for i, p in enumerate(products):
            p['id'] = i

        self._save(products)

    def toggle_active(self, product_id: int):
        products = self._load()
        for p in products:
            if p.get('id') == product_id:
                p['active'] = not p.get('active', True)
                p['status'] = 'on_shelf' if p['active'] else 'off_shelf'
        self._save(products)

    # ========= 查询 =========
    def get_all_products(self):
        return self._load()

    def get_auto_mention_products(self):
        products = self._load()
        result = []
        for p in products:
            # 兼容旧字段名 allow_injection → allow_auto_inject
            allow = p.get('allow_auto_inject', p.get('allow_injection', True))
            if p.get('active', True) and allow:
                # 复制一份，避免修改原始数据
                product_copy = dict(p)
                product_copy['allow_auto_inject'] = allow
                product_copy.pop('allow_injection', None)
                result.append(product_copy)
        return result

    def get_product_by_name(self, name: str):
        for p in self._load():
            p_name = p.get('name', '')
            if p_name.lower() == name.lower() or name.lower() in [a.lower() for a in p.get('aliases', [])]:
                return p
        return None

    def get_image_path(self, image_name: str):
        if not image_name:
            return None
        img_path = os.path.join(os.path.dirname(self.product_file), 'webui', 'static', 'uploads', image_name)
        return img_path if os.path.exists(img_path) else None


