"""装备强化与附魔系统 - 含7个bug"""
import random
from dataclasses import dataclass, field

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
        self.rng = random.Random(seed)
        self.fail_streak: dict[str, int] = {}
        self.inventory: dict[str, int] = {}

    def get_success_rate(self, level: int) -> float:
        # bug1: 线性成功率
        return 0.5

    def enhance(self, equip: Equipment, materials: int) -> tuple[bool, str]:
        if equip.enhance_level >= equip.max_enhance:
            return False, "max level"
        rate = self.get_success_rate(equip.enhance_level)
        if self.rng.random() < rate:
            equip.enhance_level += 1
            self.fail_streak[equip.eid] = 0
            return True, "success"
        else:
            # bug2: 失败装备消失无保底
            self.fail_streak[equip.eid] = self.fail_streak.get(equip.eid, 0) + 1
            if equip.enhance_level >= 10:
                return False, "destroyed"  # 装备碎了
            return False, "fail"

    def enchant(self, equip: Equipment, enchant_type: str, value: float, materials: int) -> bool:
        # bug3: 不检查附魔类型与槽位匹配
        # bug4: 不检查材料
        equip.enchant[enchant_type] = value
        return True

    def get_socket_count(self, rarity: str) -> int:
        # bug5: 固定孔数
        return 3

    def transfer_enhance(self, src: Equipment, dst: Equipment) -> bool:
        # bug6: 转移不消耗原装备
        dst.enhance_level = src.enhance_level
        return True

    def identify(self, equip: Equipment) -> dict:
        # bug7: 每次鉴定结果不同
        rng = random.Random()  # 没用seed
        affixes = {}
        affixes["atk"] = rng.randint(10, 100)
        affixes["def"] = rng.randint(10, 100)
        return affixes
