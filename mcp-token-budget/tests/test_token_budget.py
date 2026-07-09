"""Tests for MCP Token Budget — cost tracking, budgets, optimization."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPTokenBudgetServer, TOOL_DEFS
from src.token_budget_engine import TokenBudget

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>15
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==11
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"estimate_tokens","estimate_cost","log_usage","set_budget","get_budget_status","get_usage_report","list_models","optimize","get_alerts","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPTokenBudgetServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-token-budget"
        assert len(m["tools"])==11

class TestEstimateTokens:
    def test_basic(self):
        r=TokenBudget.estimate_tokens("hello world test")
        assert r>0

class TestEstimateCost:
    def test_gpt4o(self):
        r=TokenBudget.estimate_cost("gpt-4o",1000,500)
        assert r["model"]=="gpt-4o"
        assert r["total_cost"]>0
        assert r["input_cost"]>0
        assert r["output_cost"]>0
    def test_unknown_model(self):
        r=TokenBudget.estimate_cost("unknown-model",1000,500)
        assert r["total_cost"]>0

class TestLogUsage:
    def test_basic(self):
        s=TokenBudget.create_store()
        r=TokenBudget.log_usage(s,"gpt-4o",1000,500,"test_call")
        assert r["success"] is True
        assert r["cost"]>0
        assert r["label"]=="test_call"
    def test_budget_alert(self):
        s=TokenBudget.create_store()
        TokenBudget.set_budget(s, 0.001)
        r=TokenBudget.log_usage(s,"gpt-4o",100000,50000)
        assert r["budget_alert"] is not None

class TestBudget:
    def test_set_get(self):
        s=TokenBudget.create_store()
        TokenBudget.set_budget(s, 10.0)
        r=TokenBudget.get_budget_status(s)
        assert r["limit_usd"]==10.0
        assert r["remaining_usd"]==10.0
    def test_after_usage(self):
        s=TokenBudget.create_store()
        TokenBudget.set_budget(s, 1.0)
        TokenBudget.log_usage(s,"gpt-4o",100000,50000)
        r=TokenBudget.get_budget_status(s)
        assert r["spent_usd"]>0
        assert r["remaining_usd"]<1.0

class TestUsageReport:
    def test_by_model(self):
        s=TokenBudget.create_store()
        TokenBudget.log_usage(s,"gpt-4o",1000,500)
        TokenBudget.log_usage(s,"claude-sonnet-4",2000,1000)
        r=TokenBudget.get_usage_report(s,by="model")
        assert "gpt-4o" in r["data"]
        assert "claude-sonnet-4" in r["data"]
    def test_by_label(self):
        s=TokenBudget.create_store()
        TokenBudget.log_usage(s,"gpt-4o",1000,500,"chat")
        TokenBudget.log_usage(s,"gpt-4o",2000,1000,"summary")
        r=TokenBudget.get_usage_report(s,by="label")
        assert "chat" in r["data"]
        assert "summary" in r["data"]

class TestOptimize:
    def test_basic(self):
        r=TokenBudget.optimize(None,10000,5000)
        assert r["cheapest"]["total_cost"]<=r["most_expensive"]["total_cost"]
        assert r["potential_savings"]>=0
    def test_specific_models(self):
        r=TokenBudget.optimize(None,10000,5000,models=["gpt-4o","gemini-2-flash"])
        assert len(r["all"])==2
        assert r["cheapest"]["model"]=="gemini-2-flash"

class TestListModels:
    def test_list(self):
        s=TokenBudget.create_store()
        r=TokenBudget.list_models(s)
        assert "gpt-4o" in r["models"]

class TestAlerts:
    def test_alert_on_exceed(self):
        s=TokenBudget.create_store()
        TokenBudget.set_budget(s, 0.001)
        TokenBudget.log_usage(s,"gpt-4o",100000,50000)
        r=TokenBudget.get_alerts(s)
        assert r["total"]>0

class TestStatsReset:
    def test_stats(self):
        s=TokenBudget.create_store()
        TokenBudget.log_usage(s,"gpt-4o",1000,500)
        r=TokenBudget.get_stats(s)
        assert r["logged"]==1
        assert r["total_cost"]>0
    def test_reset(self):
        s=TokenBudget.create_store()
        TokenBudget.log_usage(s,"gpt-4o",1000,500)
        r=TokenBudget.reset(s)
        assert r["reset"]["logged"]==1
        assert TokenBudget.get_stats(s)["logged"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPTokenBudgetServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPTokenBudgetServer();assert "error" in json.loads(srv.handle_tool_call("estimate_cost",{}))
    def test_cost_dispatch(self):
        srv=MCPTokenBudgetServer()
        r=json.loads(srv.handle_tool_call("estimate_cost",{"model":"gpt-4o","input_tokens":1000,"output_tokens":500}))
        assert r["total_cost"]>0

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-token-budget"
