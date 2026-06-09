# product_manager/llm/injector.py

import re
from typing import List, Optional, Dict


def inject_product_info(
    context_text: str,
    product_store,
    persona_name: Optional[str] = None,
    max_similar: int = 3,
    pre_matched: Optional[List[Dict]] = None
) -> str:
    """
    根据上下文生成商品注入 Prompt（⚠️ 只返回字符串，不直接注入）
    - pre_matched: 可选，外部已匹配好的商品列表，避免重复匹配
    """

    if not product_store:
        return ""

    persona_prefix = f"[Persona]\n{persona_name}\n\n" if persona_name else ""

    if pre_matched:
        matched_products = pre_matched[:max_similar]
    else:
        products: List[Dict] = product_store.get_auto_mention_products()
        if not products:
            return ""

        matched_products: List[Dict] = []
        for p in products:
            name = p.get("name", "")
            if name and re.search(re.escape(name), context_text, re.IGNORECASE):
                matched_products.append(p)
                continue
            for alias in p.get("aliases", []):
                if alias and re.search(re.escape(alias), context_text, re.IGNORECASE):
                    matched_products.append(p)
                    break

        # 去重
        matched_products = list({p.get("name", ""): p for p in matched_products}.values())

        # 没有匹配到任何商品 → 不注入
        if not matched_products:
            return ""

        matched_products = matched_products[:max_similar]

    blocks: List[str] = []
    for p in matched_products:
        blocks.append(
            f"商品名称：{p.get('name', '未知')}\n"
            f"价格：{p.get('price', '未知')}\n"
            f"介绍：{p.get('description', '未知')}"
        )

    return persona_prefix + "\n\n".join(blocks)

