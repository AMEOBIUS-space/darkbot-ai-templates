import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from flags import FeatureFlagManager, FeatureFlag, FlagType


def test_create_boolean_flag():
    mgr = FeatureFlagManager()
    flag = mgr.create("dark_mode", FlagType.BOOLEAN, description="Dark mode toggle")
    assert flag.key == "dark_mode"
    assert flag.flag_type == FlagType.BOOLEAN


def test_is_enabled():
    mgr = FeatureFlagManager()
    mgr.create("new_ui", FlagType.BOOLEAN, percentage=100.0)
    assert mgr.is_enabled("new_ui") is True


def test_is_disabled():
    mgr = FeatureFlagManager()
    mgr.create("new_ui", FlagType.BOOLEAN, percentage=100.0)
    mgr.toggle("new_ui", False)
    assert mgr.is_enabled("new_ui") is False


def test_toggle():
    mgr = FeatureFlagManager()
    mgr.create("flag1", FlagType.BOOLEAN, percentage=100.0)
    assert mgr.toggle("flag1") is False  # Toggle off
    assert mgr.toggle("flag1") is True   # Toggle on


def test_percentage_rollout():
    mgr = FeatureFlagManager()
    mgr.create("gradual", FlagType.PERCENTAGE, percentage=50.0)
    # Hash-based — some users should get it, some shouldn't
    enabled = sum(1 for i in range(100) if mgr.is_enabled("gradual", f"user_{i}"))
    assert 30 <= enabled <= 70  # Roughly 50%


def test_percentage_consistent():
    mgr = FeatureFlagManager()
    mgr.create("gradual", FlagType.PERCENTAGE, percentage=100.0)
    # Same user always gets same result
    result1 = mgr.is_enabled("gradual", "user_42")
    result2 = mgr.is_enabled("gradual", "user_42")
    assert result1 == result2


def test_variant_ab_test():
    mgr = FeatureFlagManager()
    mgr.create("button_color", FlagType.VARIANT,
               variants=["red", "blue", "green"], default_variant="red")
    variant = mgr.get_variant("button_color", "user_123")
    assert variant in ["red", "blue", "green"]


def test_variant_consistent():
    mgr = FeatureFlagManager()
    mgr.create("ab_test", FlagType.VARIANT, variants=["A", "B"], default_variant="A")
    v1 = mgr.get_variant("ab_test", "user_99")
    v2 = mgr.get_variant("ab_test", "user_99")
    assert v1 == v2


def test_variant_disabled():
    mgr = FeatureFlagManager()
    mgr.create("ab_test", FlagType.VARIANT, variants=["A", "B"], default_variant="A")
    mgr.toggle("ab_test", False)
    assert mgr.get_variant("ab_test", "user_1") == "A"


def test_environment_targeting():
    mgr = FeatureFlagManager(current_environment="staging")
    mgr.create("staging_only", FlagType.BOOLEAN, percentage=100.0,
               environments=["staging"])
    assert mgr.is_enabled("staging_only") is True

    mgr2 = FeatureFlagManager(current_environment="production")
    mgr2.create("staging_only", FlagType.BOOLEAN, percentage=100.0,
                environments=["staging"])
    assert mgr2.is_enabled("staging_only") is False


def test_target_users():
    mgr = FeatureFlagManager()
    mgr.create("beta_feature", FlagType.BOOLEAN, percentage=0.0)
    mgr.add_target_user("beta_feature", "beta_user_1")
    assert mgr.is_enabled("beta_feature", "beta_user_1") is True
    assert mgr.is_enabled("beta_feature", "regular_user") is False


def test_excluded_users():
    mgr = FeatureFlagManager()
    mgr.create("feature", FlagType.BOOLEAN, percentage=100.0)
    mgr.add_excluded_user("feature", "banned_user")
    assert mgr.is_enabled("feature", "banned_user") is False
    assert mgr.is_enabled("feature", "normal_user") is True


def test_override():
    mgr = FeatureFlagManager()
    mgr.create("flag", FlagType.BOOLEAN, percentage=100.0)
    mgr.set_override("user_1", "flag", False)
    assert mgr.is_enabled("flag", "user_1") is False
    mgr.clear_override("user_1", "flag")
    assert mgr.is_enabled("flag", "user_1") is True


def test_set_percentage():
    mgr = FeatureFlagManager()
    mgr.create("flag", FlagType.PERCENTAGE, percentage=0.0)
    mgr.set_percentage("flag", 75.0)
    assert mgr.flags["flag"].percentage == 75.0


def test_export_import():
    mgr = FeatureFlagManager()
    mgr.create("flag1", FlagType.BOOLEAN, percentage=100.0, description="Test")
    mgr.create("flag2", FlagType.VARIANT, variants=["A", "B"], default_variant="A")
    exported = mgr.export()

    mgr2 = FeatureFlagManager()
    mgr2.import_flags(exported)
    assert "flag1" in mgr2.flags
    assert "flag2" in mgr2.flags
    assert mgr2.flags["flag2"].variants == ["A", "B"]


def test_stats():
    mgr = FeatureFlagManager()
    mgr.create("f1", FlagType.BOOLEAN, percentage=100.0)
    mgr.create("f2", FlagType.PERCENTAGE, percentage=50.0)
    mgr.toggle("f2", False)
    mgr.set_override("user1", "f1", False)
    stats = mgr.stats()
    assert stats["total_flags"] == 2
    assert stats["enabled"] == 1
    assert stats["disabled"] == 1
    assert stats["overrides"] == 1


def test_list_flags():
    mgr = FeatureFlagManager()
    mgr.create("f1", FlagType.BOOLEAN, description="First")
    mgr.create("f2", FlagType.VARIANT, variants=["A", "B"])
    flags = mgr.list_flags()
    assert len(flags) == 2
    assert flags[0]["key"] == "f1"


def test_kill_switch():
    mgr = FeatureFlagManager()
    mgr.create("emergency", FlagType.KILL_SWITCH, enabled=True)
    assert mgr.is_enabled("emergency") is True
    mgr.toggle("emergency", False)
    assert mgr.is_enabled("emergency") is False
