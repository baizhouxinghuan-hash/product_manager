import os
from astrbot.api import logger

class PersonaStore:
    def __init__(self, base_dir: str = None):
        """
        Persona 管理器
        - base_dir: persona.txt 所在目录
        """
        self.base_dir = base_dir or os.path.dirname(__file__)
        self.persona_file = os.path.join(self.base_dir, "persona.txt")
        self.personas = self._load_personas()

    def _load_personas(self):
        """
        解析 persona.txt，每行格式:
        persona_name|描述
        """
        if not os.path.exists(self.persona_file):
            logger.warning(f"[Persona] persona 文件不存在: {self.persona_file}")
            return {}

        personas = {}
        try:
            with open(self.persona_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "|" in line:
                        name, desc = line.split("|", 1)
                        personas[name.strip()] = desc.strip()
            return personas
        except Exception as e:
            logger.error(f"[Persona] 解析 persona 文件失败: {e}")
            return {}

    def get_persona(self, persona_name: str = None) -> str:
        """
        获取指定 persona 的描述（支持热重载，每次调用重新读取文件）
        - persona_name: persona 名称，None 或不存在 → 返回默认 persona
        """
        # 每次调用重新加载，支持 persona.txt 热重载
        self.personas = self._load_personas()
        if persona_name and persona_name in self.personas:
            return self.personas[persona_name]
        # 默认返回第一个 persona
        if self.personas:
            return next(iter(self.personas.values()))
        return ""

    # ========= 新增方法，兼容 main.py =========
    def get_current_persona(self) -> str:
        """
        返回当前使用的 persona 描述
        """
        return self.get_persona()


