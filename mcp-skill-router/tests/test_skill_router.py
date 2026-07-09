"""Tests for MCP Skill Router — register, route, score, learn."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPSkillRouterServer, TOOL_DEFS
from src.skill_router_engine import SkillRouter

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
        expected={"register_skill","route","record_outcome","list_skills","update_skill","remove_skill","get_routing_history","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPSkillRouterServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-skill-router"
        assert len(m["tools"])==9

class TestRegisterSkill:
    def test_basic(self):
        s=SkillRouter.create_store()
        r=SkillRouter.register_skill(s,"python_helper","Helps with Python code",keywords=["python","code","function"])
        assert r["success"] is True
    def test_with_patterns(self):
        s=SkillRouter.create_store()
        r=SkillRouter.register_skill(s,"db_tool","Database operations",keywords=["sql","database"],patterns=[r"select.*from","insert.*into"])
        assert r["success"] is True

class TestRoute:
    def test_keyword_match(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"python","Python programming",keywords=["python","function","class"])
        SkillRouter.register_skill(s,"sql","Database queries",keywords=["sql","database","query"])
        r=SkillRouter.route(s,"How do I write a Python function?")
        assert r["matched"] is True
        assert r["best_match"]=="python"
    def test_no_match(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"python","Python",keywords=["python"])
        r=SkillRouter.route(s,"What is the weather today?")
        assert r["matched"] is False
        assert r["fallback"] is True
    def test_top_k(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"a","Python code tool",keywords=["python","code"])
        SkillRouter.register_skill(s,"b","Python testing",keywords=["python","test"])
        SkillRouter.register_skill(s,"c","SQL queries",keywords=["sql"])
        r=SkillRouter.route(s,"python code test",top_k=2)
        assert len(r["results"])<=2
    def test_pattern_match(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"sql","DB tool",keywords=["sql"],patterns=[r"select.*from"])
        r=SkillRouter.route(s,"SELECT * FROM users")
        assert r["matched"] is True
        assert r["best_match"]=="sql"
    def test_priority_boost(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"low","python tool",keywords=["python"],priority=0)
        SkillRouter.register_skill(s,"high","python expert",keywords=["python"],priority=10)
        r=SkillRouter.route(s,"python help")
        assert r["best_match"]=="high"

class TestRecordOutcome:
    def test_success(self):
        s=SkillRouter.create_store()
        sid=SkillRouter.register_skill(s,"test","Test skill",keywords=["test"])["skill_id"]
        r=SkillRouter.record_outcome(s,sid,True)
        assert r["success"] is True
        assert r["usage_count"]==1
        assert r["success_rate"]==1.0
    def test_failure(self):
        s=SkillRouter.create_store()
        sid=SkillRouter.register_skill(s,"test","Test",keywords=["t"])["skill_id"]
        SkillRouter.record_outcome(s,sid,False)
        r=SkillRouter.record_outcome(s,sid,True)
        assert r["usage_count"]==2
        assert r["success_rate"]==0.5
    def test_not_found(self):
        s=SkillRouter.create_store()
        r=SkillRouter.record_outcome(s,"nonexistent",True)
        assert r["success"] is False

class TestListUpdateRemove:
    def test_list(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"a","Skill A")
        SkillRouter.register_skill(s,"b","Skill B")
        r=SkillRouter.list_skills(s)
        assert r["total"]==2
    def test_update(self):
        s=SkillRouter.create_store()
        sid=SkillRouter.register_skill(s,"test","Old desc")["skill_id"]
        r=SkillRouter.update_skill(s,sid,description="New desc",priority=5)
        assert r["success"] is True
    def test_remove(self):
        s=SkillRouter.create_store()
        sid=SkillRouter.register_skill(s,"test","Test")["skill_id"]
        r=SkillRouter.remove_skill(s,sid)
        assert r["success"] is True
        assert SkillRouter.list_skills(s)["total"]==0
    def test_remove_not_found(self):
        s=SkillRouter.create_store()
        r=SkillRouter.remove_skill(s,"nonexistent")
        assert r["success"] is False

class TestRoutingHistory:
    def test_history(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"py","Python",keywords=["python"])
        SkillRouter.route(s,"python help")
        r=SkillRouter.get_routing_history(s)
        assert r["total"]==1
        assert r["history"][0]["query"]=="python help"

class TestStatsReset:
    def test_stats(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"py","Python",keywords=["python"])
        SkillRouter.route(s,"python help")
        r=SkillRouter.get_stats(s)
        assert r["routed"]==1
        assert r["matched"]==1
    def test_reset(self):
        s=SkillRouter.create_store()
        SkillRouter.register_skill(s,"py","Python")
        SkillRouter.route(s,"test")
        r=SkillRouter.reset(s)
        assert r["reset"]["routed"]==1
        assert SkillRouter.get_stats(s)["routed"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPSkillRouterServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPSkillRouterServer();assert "error" in json.loads(srv.handle_tool_call("register_skill",{}))
    def test_register_dispatch(self):
        srv=MCPSkillRouterServer()
        r=json.loads(srv.handle_tool_call("register_skill",{"name":"test","description":"test skill"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-skill-router"
