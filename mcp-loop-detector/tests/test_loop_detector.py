"""Tests for MCP Loop Detector — record, detect, suggest, configure."""
import json, pytest, os, sys
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server import MCPLoopDetectorServer, TOOL_DEFS
from src.loop_detector_engine import LoopDetector

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
        expected={"record_action","detect_loops","suggest_breakout","get_action_history","configure","get_config","clear_actions","get_stats","reset"}
        assert names==expected

class TestManifest:
    def test_manifest(self):
        s=MCPLoopDetectorServer();m=s.manifest()
        assert m["server"]["name"]=="mcp-loop-detector"
        assert len(m["tools"])==9

class TestRecordAction:
    def test_basic(self):
        s=LoopDetector.create_store()
        r=LoopDetector.record_action(s,"read_file",{"path":"/tmp/test"})
        assert r["success"] is True
        assert r["sequence"]==0
    def test_multiple(self):
        s=LoopDetector.create_store()
        LoopDetector.record_action(s,"read_file",{"path":"/a"})
        LoopDetector.record_action(s,"write_file",{"path":"/b"})
        r=LoopDetector.record_action(s,"read_file",{"path":"/a"})
        assert r["sequence"]==2

class TestDetectLoops:
    def test_no_loop(self):
        s=LoopDetector.create_store()
        for tool in ["read","write","delete","search"]:
            LoopDetector.record_action(s,tool)
        r=LoopDetector.detect_loops(s)
        assert r["count"]==0
    def test_simple_loop(self):
        s=LoopDetector.create_store()
        for _ in range(3):
            LoopDetector.record_action(s,"read_file",{"path":"/a"})
            LoopDetector.record_action(s,"write_file",{"path":"/b"})
        r=LoopDetector.detect_loops(s)
        assert r["count"]>0
        assert r["loops"][0]["repeats"]>=2
    def test_single_tool_loop(self):
        s=LoopDetector.create_store()
        for _ in range(5):
            LoopDetector.record_action(s,"search",{"q":"test"})
        r=LoopDetector.detect_loops(s)
        assert r["count"]>0
    def test_not_enough_actions(self):
        s=LoopDetector.create_store()
        LoopDetector.record_action(s,"read")
        r=LoopDetector.detect_loops(s)
        assert r["count"]==0

class TestSuggestBreakout:
    def test_with_loop(self):
        s=LoopDetector.create_store()
        for _ in range(3):
            LoopDetector.record_action(s,"read_file",{"path":"/a"})
            LoopDetector.record_action(s,"write_file",{"path":"/b"})
        LoopDetector.detect_loops(s)
        r=LoopDetector.suggest_breakout(s)
        assert r["success"] is True
        assert len(r["suggestions"])>0
    def test_no_loops(self):
        s=LoopDetector.create_store()
        r=LoopDetector.suggest_breakout(s)
        assert r["success"] is True

class TestActionHistory:
    def test_history(self):
        s=LoopDetector.create_store()
        for i in range(5):
            LoopDetector.record_action(s,f"tool_{i}")
        r=LoopDetector.get_action_history(s,limit=3)
        assert len(r["actions"])==3
        assert r["total"]==5

class TestConfigure:
    def test_set_config(self):
        s=LoopDetector.create_store()
        r=LoopDetector.configure(s,min_cycle_len=3,max_cycle_len=10)
        assert r["config"]["min_cycle_len"]==3
        assert r["config"]["max_cycle_len"]==10
    def test_get_config(self):
        s=LoopDetector.create_store()
        r=LoopDetector.get_config(s)
        assert "min_cycle_len" in r["config"]

class TestClearActions:
    def test_clear(self):
        s=LoopDetector.create_store()
        for i in range(10):
            LoopDetector.record_action(s,f"tool_{i}")
        r=LoopDetector.clear_actions(s)
        assert r["cleared"]==10
        assert LoopDetector.get_stats(s)["total_actions"]==0

class TestStatsReset:
    def test_stats(self):
        s=LoopDetector.create_store()
        LoopDetector.record_action(s,"test")
        r=LoopDetector.get_stats(s)
        assert r["actions"]==1
    def test_reset(self):
        s=LoopDetector.create_store()
        LoopDetector.record_action(s,"test")
        r=LoopDetector.reset(s)
        assert r["reset"]["actions"]==1
        assert LoopDetector.get_stats(s)["actions"]==0

class TestDispatch:
    def test_unknown(self):
        srv=MCPLoopDetectorServer();assert "error" in json.loads(srv.handle_tool_call("nope",{}))
    def test_missing(self):
        srv=MCPLoopDetectorServer();assert "error" in json.loads(srv.handle_tool_call("record_action",{}))
    def test_record_dispatch(self):
        srv=MCPLoopDetectorServer()
        r=json.loads(srv.handle_tool_call("record_action",{"tool":"read_file"}))
        assert r["success"] is True

class TestSTDIO:
    def test_manifest_flag(self,capsys):
        from src.server import main
        with patch("sys.argv",["server","--manifest"]):main()
        parsed=json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"]=="mcp-loop-detector"
