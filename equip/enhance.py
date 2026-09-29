"""装备强化与附魔系统"""
import random
from dataclasses import dataclass, field

# 孔数按稀有度配置
SOCKETS_BY_RARITY = {
    "common": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

# 装备名 -> 槽位
SLOT_BY_NAME = {
    "sword": "weapon",
    "axe": "weapon",
    "dagger": "weapon",
    "bow": "weapon",
    "staff": "caster",
    "wand": "caster",
    "helmet": "armor",
    "armor": "armor",
    "shield": "armor",
    "ring": "accessory",
    "amulet": "accessory",
}

# 槽位 -> 允许的附魔类型
ALLOWED_ENCHANTS = {
    "weapon": {"atk", "crit", "life_steal"},
    "caster": {"spell_power", "atk", "crit"},
    "armor": {"def", "hp"},
    "accessory": {"atk", "def", "hp", "crit"},
}

ENCHANT_MATERIAL = "crystal"

# +10 及以上失败不碎装备、不降段，只掉材料
SAFE_LEVEL = 10
# 每次连续失败累积的成功率保底
PITY_BONUS = 0.05


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


class EnhanceSystem:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.fail_streak: dict[str, int] = {}
        self.inventory: dict[str, int] = {}

    def get_success_rate(self, level: int) -> float:
        # 成功率按等级指数衰减，保底5%
        return max(0.05, 0.8 * 0.9 ** level)

    def get_effective_rate(self, equip: Equipment) -> float:
        # 连续失败累积成功率（保底机制）
        streak = self.fail_streak.get(equip.eid, 0)
        return min(1.0, self.get_success_rate(equip.enhance_level) + PITY_BONUS * streak)

    def enhance(self, equip: Equipment, materials: int) -> tuple[bool, str]:
        if equip.enhance_level >= equip.max_enhance:
            return False, "max level"
        rate = self.get_effective_rate(equip)
        if self.rng.random() < rate:
            equip.enhance_level += 1
            self.fail_streak[equip.eid] = 0
            return True, "success"
        else:
            self.fail_streak[equip.eid] = self.fail_streak.get(equip.eid, 0) + 1
            # +10以上失败不降段不碎装备，只掉材料
            return False, "fail"

    def enchant(self, equip: Equipment, enchant_type: str, value: float, materials: int) -> bool:
        # 校验附魔类型与装备槽位匹配
        slot = SLOT_BY_NAME.get(equip.name, "accessory")
        if enchant_type not in ALLOWED_ENCHANTS.get(slot, set()):
            return False
        # 原子检查并预扣材料
        if self.inventory.get(ENCHANT_MATERIAL, 0) < materials:
            return False
        self.inventory[ENCHANT_MATERIAL] -= materials
        equip.enchant[enchant_type] = value
        return True

    def get_socket_count(self, rarity: str) -> int:
        return SOCKETS_BY_RARITY.get(rarity, 1)

    def transfer_enhance(self, src: Equipment, dst: Equipment) -> bool:
        if src.enhance_level <= 0:
            return False
        # 转移消耗原装备，目标不超过自身强化上限
        dst.enhance_level = min(src.enhance_level, dst.max_enhance)
        src.enhance_level = 0
        return True

    def identify(self, equip: Equipment) -> dict:
        # 固定种子确定性生成词缀，同一件装备鉴定结果一致
        rng = random.Random(f"{self.seed}:{equip.seed}")
        affixes = {}
        affixes["atk"] = rng.randint(10, 100)
        affixes["def"] = rng.randint(10, 100)
        return affixes
