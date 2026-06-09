# Changelog

## [1.0.0] - 2026-06-10

### 🎉 初始发布

Product Manager 插件首个正式版本发布。

### ✨ 新功能

- **LLM 商品智能注入** — 在对话中自动识别用户提及的商品，通过 System Prompt 注入商品信息
- **多 Persona 风格** — 支持 10 种对话风格（默认、销售、客服、冷静、热情、技术、友好、幽默、高端、极简）
- **WebUI 后台管理** — 基于 Flask 的轻量级管理界面，支持商品增删改查、图片上传、上下架管理
- **配置热重载** — 修改 AstrBot 配置面板后即时生效，无需重启插件
- **Persona 热重载** — 修改 `persona.txt` 后即时生效

### 🐛 Bug 修复

- 修复 `products.json` 字段名不统一问题（`important` → `importance`，`allow_injection` → `allow_auto_inject`）
- 修复 LLM 请求时重复匹配商品的问题（匹配逻辑只执行一次）
- 修复无匹配商品时仍注入兜底商品的问题
- 修复 `PersonaStore` 路径错误导致找不到 `persona.txt` 的问题
- 修复 `product_store.py` 原地修改原始数据的问题
- 修复 `matcher.py` / `injector.py` 中空名称匹配所有文本的问题
- 修复 `webui/server.py` 价格输入非数字时崩溃的问题
- 修复 `webui/server.py` 图片路由路径穿越漏洞
- 修复 `main.py` 中商品字段直接索引可能 KeyError 的问题

### 🔒 安全

- WebUI Session 2 小时自动过期
- 图片上传白名单校验（仅允许 jpg/png/gif/webp/bmp）
- 图片路由路径穿越防护
- 添加 `.gitignore` 排除敏感文件（密码文件、上传图片、配置文件等）

### 📚 文档

- 完善 README.md（项目概述、结构、快速开始、核心功能、配置说明、模块职责、技术栈）
- 添加 CHANGELOG.md
- 添加 LICENSE（MIT 协议）
- 添加 requirements.txt
- 添加 .gitignore