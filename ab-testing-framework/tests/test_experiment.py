import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from experiment import ABTestingFramework, ExperimentStatus


def test_create_experiment():
    fw = ABTestingFramework()
    exp = fw.create_experiment("exp1", "Button Color Test", variants=["control", "treatment"])
    assert exp.id == "exp1"
    assert "control" in exp.variants
    assert "treatment" in exp.variants


def test_start_experiment():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test")
    assert fw.start("exp1") is True
    assert fw.experiments["exp1"].status == ExperimentStatus.RUNNING


def test_assign_variant():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["A", "B"])
    fw.start("exp1")
    variant = fw.assign_variant("exp1", "user1")
    assert variant in ["A", "B"]


def test_assign_variant_consistent():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["A", "B"])
    fw.start("exp1")
    v1 = fw.assign_variant("exp1", "user42")
    v2 = fw.assign_variant("exp1", "user42")
    assert v1 == v2  # Same user always gets same variant


def test_assign_not_running():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test")  # Not started
    assert fw.assign_variant("exp1", "user1") is None


def test_track_conversion():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["control", "treatment"])
    fw.start("exp1")
    variant = fw.assign_variant("exp1", "user1")
    assert fw.track_conversion("exp1", "user1") is True
    assert fw.experiments["exp1"].variants[variant].conversions == 1


def test_track_conversion_revenue():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test")
    fw.start("exp1")
    fw.assign_variant("exp1", "user1")
    fw.track_conversion("exp1", "user1", revenue=49.99)
    variant_name = fw.get_variant("exp1", "user1")
    assert fw.experiments["exp1"].variants[variant_name].revenue == 49.99


def test_conversion_rate():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["control", "treatment"])
    fw.start("exp1")
    # Simulate: 10 visitors, 2 conversions for control
    for i in range(10):
        fw.assign_variant("exp1", f"user_{i}")
    variant = fw.get_variant("exp1", "user_0")
    fw.track_conversion("exp1", "user_0")
    fw.track_conversion("exp1", "user_1")  # May or may not be same variant
    rate = fw.conversion_rate("exp1", variant)
    assert isinstance(rate, float)


def test_z_score():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["control", "treatment"])
    fw.start("exp1")
    # Simulate enough data
    for i in range(200):
        v = fw.assign_variant("exp1", f"user_{i}")
    # Add conversions
    for i in range(50):
        fw.track_conversion("exp1", f"user_{i}")
    z = fw.z_score("exp1")
    assert z is not None


def test_results():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["control", "treatment"])
    fw.start("exp1")
    for i in range(100):
        fw.assign_variant("exp1", f"user_{i}")
    for i in range(30):
        fw.track_conversion("exp1", f"user_{i}")
    results = fw.results("exp1")
    assert "variants" in results
    assert "total_visitors" in results
    assert results["total_visitors"] == 100


def test_set_weights():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["A", "B"])
    fw.set_weights("exp1", {"A": 80.0, "B": 20.0})
    assert fw.experiments["exp1"].variants["A"].weight == 80.0


def test_stop():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test")
    fw.start("exp1")
    assert fw.stop("exp1") is True
    assert fw.experiments["exp1"].status == ExperimentStatus.STOPPED


def test_complete():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test")
    fw.start("exp1")
    fw.complete("exp1")
    assert fw.experiments["exp1"].status == ExperimentStatus.COMPLETED


def test_stats():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test")
    fw.create_experiment("exp2", "Test2")
    fw.start("exp1")
    stats = fw.stats()
    assert stats["total_experiments"] == 2
    assert stats["running"] == 1


def test_is_significant():
    fw = ABTestingFramework()
    fw.create_experiment("exp1", "Test", variants=["control", "treatment"])
    fw.start("exp1")
    sig = fw.is_significant("exp1")
    assert isinstance(sig, bool)
