"""Tests for MCP Prompt Versioning — create, save, diff, rollback, branch."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPPromptVersioningServer, TOOL_DEFS
from src.prompt_versioning_engine import PromptVersioning

class TestToolDefs:
    def test_names(self):
        for t in TOOL_DEFS: assert "name" in t and len(t["name"])>0
    def test_descs(self):
        for t in TOOL_DEFS: assert "description" in t and len(t["description"])>15
    def test_schema(self):
        for t in TOOL_DEFS: assert "inputSchema" in t and t["inputSchema"]["type"]=="object"
    def test_count(self):
        assert len(TOOL_DEFS)==13
    def test_required(self):
        names={t["name"] for t in TOOL_DEFS}
        expected={"create_prompt","save_version","get_version","get_active","rollback","diff","list_versions","list_prompts","branch","compare_effectiveness","delete_prompt","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPPromptVersioningServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-prompt-versioning"
        assert len(m["tools"])==13

class TestCreatePrompt:
    def test_basic(self):
        s=PromptVersioning.create_store()
        r=PromptVersioning.create_prompt(s,"greeting","Hello world")
        assert r["success"] is True
        assert r["version_id"]=="v1"
    def test_with_metadata(self):
        s=PromptVersioning.create_store()
        r=PromptVersioning.create_prompt(s,"test","text",{"model":"gpt-4"})
        assert r["success"] is True

class TestSaveVersion:
    def test_basic(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","v1 text")["prompt_id"]
        r=PromptVersioning.save_version(s,pid,"v2 text",message="updated")
        assert r["success"] is True
        assert r["version_id"]=="v2"
    def test_not_found(self):
        s=PromptVersioning.create_store()
        r=PromptVersioning.save_version(s,"nonexistent","text")
        assert r["success"] is False

class TestGetVersion:
    def test_active(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","hello")["prompt_id"]
        r=PromptVersioning.get_active(s,pid)
        assert r["success"] is True
        assert r["version"]["text"]=="hello"
    def test_specific(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","v1")["prompt_id"]
        PromptVersioning.save_version(s,pid,"v2")
        r=PromptVersioning.get_version(s,pid,"v1")
        assert r["version"]["text"]=="v1"
        assert r["is_active"] is False
    def test_not_found(self):
        s=PromptVersioning.create_store()
        r=PromptVersioning.get_version(s,"nonexistent")
        assert r["success"] is False

class TestRollback:
    def test_basic(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","v1")["prompt_id"]
        PromptVersioning.save_version(s,pid,"v2")
        r=PromptVersioning.rollback(s,pid,"v1")
        assert r["success"] is True
        assert r["new_active"]=="v1"
        active=PromptVersioning.get_active(s,pid)
        assert active["version"]["text"]=="v1"
    def test_not_found(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","v1")["prompt_id"]
        r=PromptVersioning.rollback(s,pid,"v99")
        assert r["success"] is False

class TestDiff:
    def test_different(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","hello world")["prompt_id"]
        PromptVersioning.save_version(s,pid,"hello earth")
        r=PromptVersioning.diff(s,pid,"v1","v2")
        assert r["success"] is True
        assert not r["identical"]
        assert r["additions"]>=1
        assert r["deletions"]>=1
    def test_identical(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","same text")["prompt_id"]
        PromptVersioning.save_version(s,pid,"same text")
        r=PromptVersioning.diff(s,pid,"v1","v2")
        assert r["identical"] is True

class TestListVersions:
    def test_basic(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","v1")["prompt_id"]
        PromptVersioning.save_version(s,pid,"v2")
        PromptVersioning.save_version(s,pid,"v3")
        r=PromptVersioning.list_versions(s,pid)
        assert r["total"]==3
        assert r["versions"][2]["is_active"] is True

class TestListPrompts:
    def test_basic(self):
        s=PromptVersioning.create_store()
        PromptVersioning.create_prompt(s,"p1","text1")
        PromptVersioning.create_prompt(s,"p2","text2")
        r=PromptVersioning.list_prompts(s)
        assert r["total"]==2

class TestBranch:
    def test_basic(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","v1")["prompt_id"]
        PromptVersioning.save_version(s,pid,"v2")
        r=PromptVersioning.branch(s,pid,"experiment",from_version="v1")
        assert r["success"] is True
        assert r["base_version"]=="v1"

class TestCompareEffectiveness:
    def test_basic(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","prompt A")["prompt_id"]
        PromptVersioning.save_version(s,pid,"prompt B")
        r=PromptVersioning.compare_effectiveness(s,pid,"v1","v2",0.7,0.85)
        assert r["success"] is True
        assert r["winner"]=="v2"
        assert r["delta"]==0.15

class TestDeletePrompt:
    def test_basic(self):
        s=PromptVersioning.create_store()
        pid=PromptVersioning.create_prompt(s,"p","text")["prompt_id"]
        r=PromptVersioning.delete_prompt(s,pid)
        assert r["success"] is True
        assert PromptVersioning.list_prompts(s)["total"]==0

class TestStatsReset:
    def test_stats(self):
        s=PromptVersioning.create_store()
        PromptVersioning.create_prompt(s,"p","text")
        r=PromptVersioning.get_stats(s)
        assert r["saved"]==1
    def test_reset(self):
        s=PromptVersioning.create_store()
        PromptVersioning.create_prompt(s,"p","text")
        r=PromptVersioning.reset(s)
        assert r["reset"]["saved"]==1
        assert PromptVersioning.get_stats(s)["saved"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPPromptVersioningServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPPromptVersioningServer();assert "error" in json.loads(srv.handle_tool_call("create_prompt",{}))
    def test_create_dispatch(self):
        srv=MCPPromptVersioningServer()
        r=json.loads(srv.handle_tool_call("create_prompt",{"name":"test","text":"hello"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-prompt-versioning"
