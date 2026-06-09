import os
from ..persona.persona_store import PersonaStore
from .matcher import match_products

# 正确指向 persona/ 目录
_persona_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persona')
persona_store = PersonaStore(_persona_dir)

def build_prompt(user_message: str, product_store, persona_name: str = None, max_products: int = 3):
    """
    根据用户输入和当前 persona 构建 prompt
    - user_message: 用户消息文本
    - product_store: ProductStore 实例
    - persona_name: 指定 persona 名称，如果为 None 则使用默认 persona
    - max_products: 注入的最大商品数量
    """

    # 获取 persona 描述
    persona_desc = persona_store.get_persona(persona_name)
    if not persona_desc:
        persona_desc = "你是一个友好、专业的助理。"

    # 匹配商品
    matched_products = match_products(
        context_text=user_message,
        product_store=product_store,
        max_results=max_products
    )

    # 构建商品信息文本（仅供 LLM 思考）
    product_info_lines = []
    for p in matched_products:
        info_line = (
            f"商品名称: {p.get('name', '未知')}, "
            f"价格: {p.get('price', '未知')}, "
            f"介绍: {p.get('description', '未知')}"
        )
        product_info_lines.append(info_line)

    product_info_text = ""
    if product_info_lines:
        product_info_text = (
            "以下是可能相关的商品信息（仅用于内部参考，不必直接输出给用户）：\n"
            + "\n".join(product_info_lines)
            + "\n"
        )

    # 最终 prompt
    prompt = (
        f"{persona_desc}\n"
        f"用户输入: {user_message}\n"
        f"{product_info_text}"
        f"请根据以上信息生成回复。"
    )

    return prompt

