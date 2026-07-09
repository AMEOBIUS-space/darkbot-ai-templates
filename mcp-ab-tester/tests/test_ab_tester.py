"""Tests for MCP AB Tester — create, trial, results, significance."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPABTesterServer, TOOL_DEFS
from src.ab_tester_engine import ABTester

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>15
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==9
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"create_experiment","record_trial","get_results","compute_significance","complete_experiment","list_experiments","delete_experiment","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPABTesterServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-ab-tester"
        assert len(m["tools"])==9

class TestCreateExperiment:
    def test_basic(self):
        s=ABTester.create_store()
        r=ABTester.create_experiment(s,"prompt_test")
        assert r["success"] is True
        assert r["variants"]==2  # default A/B
    def test_custom_variants(self):
        s=ABTester.create_store()
        variants=[{"id":"A","label":"short"},{"id":"B","label":"long"},{"id":"C","label":"medium"}]
        r=ABTester.create_experiment(s,"multi_test",variants=variants)
        assert r["variants"]==3

class TestRecordTrial:
    def test_basic(self):
        s=ABTester.create_store()
        eid=ABTester.create_experiment(s,"test")["experiment_id"]
        r=ABTester.record_trial(s,eid,"A",True,score=0.9)
        assert r["success"] is True
        assert r["total_trials"]==1
    def test_not_found(self):
        s=ABTester.create_store()
        r=ABTester.record_trial(s,"nonexistent","A",True)
        assert r["success"] is False

class TestGetResults:
    def test_basic(self):
        s=ABTester.create_store()
        eid=ABTester.create_experiment(s,"test")["experiment_id"]
        ABTester.record_trial(s,eid,"A",True,score=0.9)
        ABTester.record_trial(s,eid,"A",False,score=0.3)
        ABTester.record_trial(s,eid,"B",True,score=0.8)
        r=ABTester.get_results(s,eid)
        assert r["variants"]["A"]["trials"]==2
        assert r["variants"]["A"]["success_rate"]==0.5
        assert r["total_trials"]==3

class TestComputeSignificance:
    def test_significant(self):
        s=ABTester.create_store()
        eid=ABTester.create_experiment(s,"test")["experiment_id"]
        # A: 18/20 success, B: 8/20 success
        for _ in range(18): ABTester.record_trial(s,eid,"A",True)
        for _ in range(2): ABTester.record_trial(s,eid,"A",False)
        for _ in range(8): ABTester.record_trial(s,eid,"B",True)
        for _ in range(12): ABTester.record_trial(s,eid,"B",False)
        r=ABTester.compute_significance(s,eid)
        assert r["significant"] is True
        assert r["winner"]=="A"
    def test_not_significant(self):
        s=ABTester.create_store()
        eid=ABTester.create_experiment(s,"test")["experiment_id"]
        ABTester.record_trial(s,eid,"A",True)
        ABTester.record_trial(s,eid,"B",True)
        r=ABTester.compute_significance(s,eid)
        assert r["significant"] is False

class TestCompleteExperiment:
    def test_basic(self):
        s=ABTester.create_store()
        eid=ABTester.create_experiment(s,"test")["experiment_id"]
        ABTester.record_trial(s,eid,"A",True)
        r=ABTester.complete_experiment(s,eid,winner="A")
        assert r["success"] is True
        assert r["winner"]=="A"

class TestListExperiments:
    def test_list(self):
        s=ABTester.create_store()
        ABTester.create_experiment(s,"e1")
        ABTester.create_experiment(s,"e2")
        r=ABTester.list_experiments(s)
        assert r["total"]==2

class TestDeleteExperiment:
    def test_delete(self):
        s=ABTester.create_store()
        eid=ABTester.create_experiment(s,"test")["experiment_id"]
        r=ABTester.delete_experiment(s,eid)
        assert r["success"] is True
        assert ABTester.list_experiments(s)["total"]==0

class TestStatsReset:
    def test_stats(self):
        s=ABTester.create_store()
        ABTester.create_experiment(s,"test")
        r=ABTester.get_stats(s)
        assert r["experiments"]==1
    def test_reset(self):
        s=ABTester.create_store()
        ABTester.create_experiment(s,"test")
        r=ABTester.reset(s)
        assert r["reset"]["experiments"]==1
        assert ABTester.get_stats(s)["experiments"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPABTesterServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPABTesterServer();assert "error" in json.loads(srv.handle_tool_call("create_experiment",{}))
    def test_create_dispatch(self):
        srv=MCPABTesterServer()
        r=json.loads(srv.handle_tool_call("create_experiment",{"name":"test"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-ab-tester"
