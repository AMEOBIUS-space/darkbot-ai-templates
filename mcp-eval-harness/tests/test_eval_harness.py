"""Tests for MCP Eval Harness — suites, evaluation, regression, reports."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPEvalHarnessServer, TOOL_DEFS
from src.eval_harness_engine import EvalHarness

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>15
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==10
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"create_suite","add_test","evaluate_response","run_suite","set_baseline","check_regression","get_report","list_suites","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPEvalHarnessServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-eval-harness"
        assert len(m["tools"])==10

class TestCreateSuite:
    def test_basic(self):
        s=EvalHarness.create_store()
        r=EvalHarness.create_suite(s,name="test_suite",description="My tests")
        assert r["success"] is True
        assert r["test_count"]==0
    def test_with_tests(self):
        s=EvalHarness.create_store()
        tests=[{"name":"t1","prompt":"hello","expected":"hi"}]
        r=EvalHarness.create_suite(s,name="suite",tests=tests)
        assert r["test_count"]==1

class TestAddTest:
    def test_basic(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        r=EvalHarness.add_test(s,sid,"test1","prompt","expected","contains")
        assert r["success"] is True
    def test_suite_not_found(self):
        s=EvalHarness.create_store()
        r=EvalHarness.add_test(s,"nonexistent","test","prompt")
        assert r["success"] is False

class TestEvaluateResponse:
    def test_contains_pass(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"hello world","world","contains")
        assert r["passed"] is True
        assert r["score"]==10
    def test_contains_fail(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"hello","world","contains")
        assert r["passed"] is False
    def test_exact(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"hello","hello","exact")
        assert r["passed"] is True
    def test_regex(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"test123","\\d+","regex")
        assert r["passed"] is True
    def test_json_valid(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,'{"key":"val"}',"","json_valid")
        assert r["passed"] is True
    def test_json_invalid(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"not json","","json_valid")
        assert r["passed"] is False
    def test_starts_with(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"Hello world","hello","starts_with")
        assert r["passed"] is True
    def test_keyword_count(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"Python is great and fast","Python,great,fast","keyword_count")
        assert r["score"]==10
    def test_length(self):
        s=EvalHarness.create_store()
        r=EvalHarness.evaluate_response(s,"a"*50,"10:100","length")
        assert r["passed"] is True

class TestRunSuite:
    def test_basic(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.add_test(s,sid,"t2","world","world")
        r=EvalHarness.run_suite(s,sid,["hello","world"])
        assert r["passed"]==2
        assert r["pass_rate"]==1.0
    def test_partial(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.add_test(s,sid,"t2","world","world")
        r=EvalHarness.run_suite(s,sid,["hello","wrong"])
        assert r["passed"]==1
        assert r["failed"]==1
    def test_no_responses(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        r=EvalHarness.run_suite(s,sid)
        assert "message" in r

class TestBaselineRegression:
    def test_set_baseline(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.run_suite(s,sid,["hello"])
        r=EvalHarness.set_baseline(s,sid)
        assert r["baseline"]==100.0
    def test_check_regression_stable(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.run_suite(s,sid,["hello"])
        EvalHarness.set_baseline(s,sid)
        EvalHarness.run_suite(s,sid,["hello"])
        r=EvalHarness.check_regression(s,sid)
        assert r["stable"] is True
    def test_check_regression_regressed(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.add_test(s,sid,"t2","world","world")
        EvalHarness.run_suite(s,sid,["hello","world"])
        EvalHarness.set_baseline(s,sid)
        EvalHarness.run_suite(s,sid,["hello","wrong"])
        r=EvalHarness.check_regression(s,sid)
        assert r["regressed"] is True

class TestReport:
    def test_suite_report(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="my_suite")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.run_suite(s,sid,["hello"])
        r=EvalHarness.get_report(s,sid)
        assert r["total_runs"]==1
        assert r["latest_score"]==100.0
    def test_aggregate_report(self):
        s=EvalHarness.create_store()
        sid=EvalHarness.create_suite(s,name="s")["suite_id"]
        EvalHarness.add_test(s,sid,"t1","hello","hello")
        EvalHarness.run_suite(s,sid,["hello"])
        r=EvalHarness.get_report(s)
        assert r["total_suites"]==1
        assert r["total_runs"]==1

class TestListSuites:
    def test_list(self):
        s=EvalHarness.create_store()
        EvalHarness.create_suite(s,name="s1")
        EvalHarness.create_suite(s,name="s2")
        r=EvalHarness.list_suites(s)
        assert r["total"]==2

class TestStatsReset:
    def test_stats(self):
        s=EvalHarness.create_store()
        EvalHarness.evaluate_response(s,"hello","hello")
        r=EvalHarness.get_stats(s)
        assert r["tests_run"]==1
        assert r["passed"]==1
    def test_reset(self):
        s=EvalHarness.create_store()
        EvalHarness.create_suite(s,name="s")
        EvalHarness.evaluate_response(s,"hello","hello")
        r=EvalHarness.reset(s)
        assert r["reset"]["tests_run"]==1
        assert EvalHarness.get_stats(s)["tests_run"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPEvalHarnessServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPEvalHarnessServer();assert "error" in json.loads(srv.handle_tool_call("create_suite",{}))
    def test_create_dispatch(self):
        srv=MCPEvalHarnessServer()
        r=json.loads(srv.handle_tool_call("create_suite",{"name":"test"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-eval-harness"
