# product_manager/main.py

import os
import asyncio
from typing import List

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.provider import ProviderRequest
from astrbot.api import logger, AstrBotConfig

from .catalog.product_store import ProductStore
from .persona.persona_store import PersonaStore
from .llm.matcher import match_products
from .llm.injector import inject_product_info
from .webui import server as webui_server


@register(
    "product_manager",
    "you",
    "商品管理 + WebUI + LLM 商品注入插件",
    "1.0.0",
    "local"
)
class ProductManager(Star):

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.context = context
        self.config = config

        self.plugin_dir = os.path.dirname(__file__)
        self.product_store = ProductStore()
        self.persona_store = PersonaStore(self.plugin_dir)

        self._webui_started = False

        asyncio.create_task(self._start_webui())
        logger.info("✅ ProductManager 插件初始化完成")

    def _get_config(self, key: str, default=None):
        """支持热重载的配置读取，每次调用时从 self.config 实时读取"""
        return self.config.get(key, default)

    async def _start_webui(self):
        if self._webui_started:
            return
        try:
            webui_server.run_webui(product_store=self.product_store)
            self._webui_started = True
            logger.info("🌐 商品后台 WebUI 已启动：http://127.0.0.1:5465")
        except Exception as e:
            logger.error(f"WebUI 启动失败: {e}", exc_info=True)

    # =========================================================
    # LLM 请求前：注入商品信息
    # =========================================================
    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        user_text = event.message_str
        if not user_text:
            return

        # 检查全局 allow_auto_inject 开关（热重载）
        if not self._get_config("allow_auto_inject", True):
            return

        # 读取热重载配置
        max_match = self._get_config("max_match_products", 3)

        # 是否有可能命中商品（只做一次匹配，不再重复）
        matched = match_products(
            context_text=user_text,
            product_store=self.product_store,
            max_results=max_match
        )
        if not matched:
            return

        persona_text = self.persona_store.get_persona()

        # ✅ 生成商品 Prompt（字符串，传入已匹配结果避免重复匹配）
        product_prompt = inject_product_info(
            context_text=user_text,
            product_store=self.product_store,
            persona_name=persona_text,
            max_similar=max_match,
            pre_matched=matched
        )

        if not product_prompt:
            return

        # ✅ 真正注入到 LLM
        try:
            req.add_system_prompt(product_prompt)
        except Exception:
            # 兼容旧 Provider
            req.prompt = product_prompt + "\n\n" + getattr(req, "prompt", "")

    # =========================================================
    # 命令：查看所有商品
    # =========================================================
    @filter.command("查看所有商品")
    async def cmd_list_products(self, event: AstrMessageEvent):
        products = self.product_store.get_all_products()
        if not products:
            yield event.plain_result("当前没有任何商品。")
            return

        lines: List[str] = ["📦 当前商品列表："]
        for p in products:
            lines.append(
                f"- {p.get('name', '未知')} | 价格：{p.get('price', '未知')} | "
                f"{'上架' if p.get('active', True) else '下架'}"
            )
        yield event.plain_result("\n".join(lines))

    # =========================================================
    # 命令：查看商品
    # =========================================================
    @filter.command("查看商品")
    async def cmd_view_product(self, event: AstrMessageEvent, name: str):
        product = self.product_store.get_product_by_name(name)
        if not product:
            yield event.plain_result(f"未找到商品：{name}")
            return

        text = (
            f"📦 商品信息\n"
            f"名称：{product.get('name', '未知')}\n"
            f"价格：{product.get('price', '未知')}\n"
            f"介绍：{product.get('description', '未知')}"
        )
        yield event.plain_result(text)

        if product.get("image"):
            path = self.product_store.get_image_path(product["image"])
            if path:
                yield event.image_result(path)

    async def terminate(self):
        logger.info("🛑 ProductManager 插件已停止")