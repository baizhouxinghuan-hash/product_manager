import re
from typing import List, Dict

def match_products(context_text: str, product_store, max_results: int = 5) -> List[Dict]:
    """
    匹配用户输入文本中的商品
    - context_text: 用户输入
    - product_store: ProductStore 实例
    - max_results: 最大返回数量
    """
    if not product_store:
        raise ValueError("match_products 必须传入 product_store 实例")

    products: List[Dict] = product_store.get_auto_mention_products()
    matched: List[Dict] = []

    for p in products:
        name = p.get('name', '')
        if name and re.search(re.escape(name), context_text, re.IGNORECASE):
            matched.append(p)
            continue
        for alias in p.get('aliases', []):
            if alias and re.search(re.escape(alias), context_text, re.IGNORECASE):
                matched.append(p)
                break

    # 去重（按 name）
    matched = list({p.get('name', ''): p for p in matched}.values())

    # 按重要度排序，如果 importance 是 dict，则取最大值
    def importance_key(p):
        imp = p.get('importance', 0)
        if isinstance(imp, dict):
            return max(imp.values())
        return imp

    matched = sorted(matched, key=importance_key, reverse=True)

    return matched[:max_results]


