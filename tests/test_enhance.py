"""装备强化与附魔系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from equip.enhance import EnhanceSystem, Equipment

class TestSuccessRate:
    def test_rate_decreases_with_level(self):
        es = EnhanceSystem()
        r1 = es.get_success_rate(1)
        r14 = es.get_success_rate(14)
        assert r14 < r1  # bug1: 都是0.5

class TestDestroyPity:
    def test_high_enhance_fail_not_destroyed(self):
        es = EnhanceSystem(seed=1)
        e = Equipment("e1", "sword", "legendary", enhance_level=14)
        # 连续失败应该有保底，不应该碎
        for _ in range(20):
            success, msg = es.enhance(e, 1)
            if success:
                break
        assert e.enhance_level >= 14  # bug2: 可能被destroyed
        assert msg != "destroyed" or e.enhance_level == 15

class TestEnchantTypeCheck:
    def test_weapon_cannot_enchant_spell_power(self):
        es = EnhanceSystem()
        weapon = Equipment("w1", "sword", "epic")
        # 武器不能附魔法术强度
        result = es.enchant(weapon, "spell_power", 50, 1)
        assert result == False  # bug3: 返回True

class TestMaterialCheck:
    def test_enchant_requires_materials(self):
        es = EnhanceSystem()
        es.inventory = {"crystal": 0}
        e = Equipment("e1", "ring", "rare")
        result = es.enchant(e, "atk", 10, 1)  # 需要1个crystal
        assert result == False  # bug4: 材料不够也成功

class TestSocketByRarity:
    def test_legendary_has_more_sockets(self):
        es = EnhanceSystem()
        assert es.get_socket_count("legendary") > es.get_socket_count("common")  # bug5: 都是3

class TestTransferConsumesSource:
    def test_transfer_consumes_source(self):
        es = EnhanceSystem()
        src = Equipment("s1", "old", "epic", enhance_level=10)
        dst = Equipment("d1", "new", "epic", enhance_level=0)
        es.transfer_enhance(src, dst)
        assert dst.enhance_level == 10
        assert src.enhance_level == 0  # bug6: 原装备还是10

class TestIdentifyDeterministic:
    def test_identify_same_seed_same_result(self):
        es = EnhanceSystem(seed=42)
        e1 = Equipment("e1", "item", "rare", seed=12345)
        e2 = Equipment("e2", "item", "rare", seed=12345)
        r1 = es.identify(e1)
        r2 = es.identify(e2)
        assert r1 == r2  # bug7: 随机种子不同结果不同
