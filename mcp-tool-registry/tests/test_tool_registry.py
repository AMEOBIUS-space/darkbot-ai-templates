"""Tests for MCP Tool Registry — register, search, health, categories."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPToolRegistryServer, TOOL_DEFS
from src.tool_registry_engine import ToolRegistry

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>15
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==12
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"register","unregister","enable","disable","record_call","get_tool","list_tools","search","health_check","get_categories","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPToolRegistryServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-tool-registry"
        assert len(m["tools"])==12

class TestRegister:
    def test_basic(self):
        s=ToolRegistry.create_store()
        r=ToolRegistry.register(s,"read_file",description="Read a file",category="filesystem")
        assert r["success"] is True
    def test_with_tags(self):
        s=ToolRegistry.create_store()
        r=ToolRegistry.register(s,"search",description="Search",tags=["web","api"])
        assert r["success"] is True

class TestUnregister:
    def test_basic(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        r=ToolRegistry.unregister(s,"test")
        assert r["success"] is True
    def test_not_found(self):
        s=ToolRegistry.create_store()
        r=ToolRegistry.unregister(s,"nonexistent")
        assert r["success"] is False

class TestEnableDisable:
    def test_disable(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        r=ToolRegistry.disable(s,"test")
        assert r["enabled"] is False
    def test_enable(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        ToolRegistry.disable(s,"test")
        r=ToolRegistry.enable(s,"test")
        assert r["enabled"] is True

class TestRecordCall:
    def test_success(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        r=ToolRegistry.record_call(s,"test",True,100)
        assert r["usage_count"]==1
        assert r["success_rate"]==1.0
    def test_failure(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        ToolRegistry.record_call(s,"test",False,200)
        r=ToolRegistry.record_call(s,"test",True,150)
        assert r["usage_count"]==2

class TestSearch:
    def test_by_name(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"read_file",description="Read")
        ToolRegistry.register(s,"write_file",description="Write")
        r=ToolRegistry.search(s,"file")
        assert len(r["results"])>=2
    def test_by_tag(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"api_call",description="Call API",tags=["network","http"])
        r=ToolRegistry.search(s,"network")
        assert len(r["results"])==1

class TestHealthCheck:
    def test_single(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        ToolRegistry.record_call(s,"test",True,100)
        r=ToolRegistry.health_check(s,"test")
        assert r["status"]=="healthy"
    def test_all(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"a")
        ToolRegistry.register(s,"b")
        r=ToolRegistry.health_check(s)
        assert r["total"]==2

class TestListTools:
    def test_all(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"a",category="x")
        ToolRegistry.register(s,"b",category="y")
        r=ToolRegistry.list_tools(s)
        assert r["total"]==2
    def test_by_category(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"a",category="fs")
        ToolRegistry.register(s,"b",category="net")
        r=ToolRegistry.list_tools(s,category="fs")
        assert r["total"]==1

class TestCategories:
    def test_list(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"a",category="fs")
        ToolRegistry.register(s,"b",category="net")
        r=ToolRegistry.get_categories(s)
        assert r["total"]==2

class TestStatsReset:
    def test_stats(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        ToolRegistry.record_call(s,"test",True)
        r=ToolRegistry.get_stats(s)
        assert r["total_tools"]==1
        assert r["called"]==1
    def test_reset(self):
        s=ToolRegistry.create_store()
        ToolRegistry.register(s,"test")
        r=ToolRegistry.reset(s)
        assert r["reset"]["total_tools"]==1
        assert ToolRegistry.get_stats(s)["total_tools"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPToolRegistryServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPToolRegistryServer();assert "error" in json.loads(srv.handle_tool_call("register",{}))
    def test_register_dispatch(self):
        srv=MCPToolRegistryServer()
        r=json.loads(srv.handle_tool_call("register",{"name":"test_tool"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-tool-registry"
