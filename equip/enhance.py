"""装备强化与附魔系统"""
import random
from dataclasses import dataclass, field

# 各槽位允许的附魔类型
SLOT_ENCHANT_RULES: dict[str, set[str]] = {
    "weapon": {"atk", "crit", "penetration", "life_steal"},
    "armor": {"def", "hp", "spell_power", "cooldown"},
    "accessory": {"atk", "def", "hp", "crit", "spell_power"},
}

# 装备名 -> 槽位 关键词
_SLOT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "weapon": ("sword", "axe", "bow", "dagger", "staff", "wand", "blade", "hammer", "spear"),
    "armor": ("armor", "helm", "helmet", "boots", "gloves", "shield", "chest", "robe"),
    "accessory": ("ring", "amulet", "necklace", "belt", "trinket", "charm"),
}

# 稀有度 -> 孔数
RARITY_SOCKETS: dict[str, int] = {
    "common": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

ENCHANT_MATERIAL = "crystal"

# 强化成功率: base * decay ** level, 指数衰减
_BASE_RATE = 0.95
_RATE_DECAY = 0.82
# 保底: 每次连续失败累积的成功率加成
_PITY_BONUS = 0.08
# +10 及以上失败不掉段不碎装备, 只掉材料
_SAFE_LEVEL = 10


@dataclass
class Equipment:
    eid: str
    name: str
    rarity: str  # common/rare/epic/legendary
    enhance_level: int = 0
    max_enhance: int = 15
    enchant: dict = field(default_factory=dict)
    sockets: int = 0
    seed: int = 0


def _slot_of(equip: Equipment) -> str:
    name = equip.name.lower()
    for slot, keywords in _SLOT_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return slot
    return "accessory"


class EnhanceSystem:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.fail_streak: dict[str, int] = {}
        self.inventory: dict[str, int] = {}

    def get_success_rate(self, level: int) -> float:
        # 成功率随等级指数衰减
        return _BASE_RATE * (_RATE_DECAY ** level)

    def _effective_rate(self, equip: Equipment) -> float:
        # 保底机制: 连续失败累积成功率
        streak = self.fail_streak.get(equip.eid, 0)
        return min(1.0, self.get_success_rate(equip.enhance_level) + streak * _PITY_BONUS)

    def enhance(self, equip: Equipment, materials: int) -> tuple[bool, str]:
        if equip.enhance_level >= equip.max_enhance:
            return False, "max level"
        rate = self._effective_rate(equip)
        if self.rng.random() < rate:
            equip.enhance_level += 1
            self.fail_streak[equip.eid] = 0
            return True, "success"
        # 失败: 累积保底, 装备不销毁不降段, 只消耗材料
        self.fail_streak[equip.eid] = self.fail_streak.get(equip.eid, 0) + 1
        if equip.enhance_level >= _SAFE_LEVEL:
            return False, "fail_materials_lost"
        return False, "fail"

    def enchant(self, equip: Equipment, enchant_type: str, value: float, materials: int) -> bool:
        # 校验附魔类型与装备槽位匹配
        slot = _slot_of(equip)
        if enchant_type not in SLOT_ENCHANT_RULES.get(slot, set()):
            return False
        # 原子检查并预扣材料, 材料不足直接失败
        if self.inventory.get(ENCHANT_MATERIAL, 0) < materials:
            return False
        self.inventory[ENCHANT_MATERIAL] -= materials
        equip.enchant[enchant_type] = value
        return True

    def get_socket_count(self, rarity: str) -> int:
        # 孔数按稀有度配置
        return RARITY_SOCKETS.get(rarity, RARITY_SOCKETS["common"])

    def transfer_enhance(self, src: Equipment, dst: Equipment) -> bool:
        if src.enhance_level <= 0:
            return False
        # 转移消耗原装备强化等级, 目标不超过自身上限
        dst.enhance_level = min(src.enhance_level, dst.max_enhance)
        src.enhance_level = 0
        self.fail_streak.pop(src.eid, None)
        return True

    def identify(self, equip: Equipment) -> dict:
        # 固定种子确定性生成词缀, 同一件装备鉴定结果一致
        rng = random.Random(equip.seed)
        affixes = {}
        affixes["atk"] = rng.randint(10, 100)
        affixes["def"] = rng.randint(10, 100)
        return affixes
