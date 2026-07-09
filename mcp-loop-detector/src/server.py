"""MCP Server for Loop Detector — detect and break agent action cycles."""
import json, sys, argparse
from .loop_detector_engine import LoopDetector

_store = LoopDetector.create_store()

TOOL_DEFS = [
    {"name":"record_action","description":"Record an agent action for loop detection.","inputSchema":{"type":"object","properties":{"tool":{"type":"string"},"args":{"type":"object"},"result_summary":{"type":"string","default":""}},"required":["tool"]}},
    {"name":"detect_loops","description":"Analyze recent actions for repeating patterns.","inputSchema":{"type":"object","properties":{"window":{"type":"integer"}},"required":[]}},
    {"name":"suggest_breakout","description":"Get suggestions for breaking out of a detected loop.","inputSchema":{"type":"object","properties":{"loop_id":{"type":"string"}},"required":[]}},
    {"name":"get_action_history","description":"Get recent action history.","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","default":20}},"required":[]}},
    {"name":"configure","description":"Configure loop detection parameters.","inputSchema":{"type":"object","properties":{"min_cycle_len":{"type":"integer"},"max_cycle_len":{"type":"integer"},"min_repeats":{"type":"integer"},"window_size":{"type":"integer"}},"required":[]}},
    {"name":"get_config","description":"Get current configuration.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"clear_actions","description":"Clear action history.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"get_stats","description":"Get loop detection statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all actions, loops, and stats.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPLoopDetectorServer:
    def __init__(self,name="mcp-loop-detector",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="record_action":return json.dumps(LoopDetector.record_action(_store,args["tool"],args.get("args"),args.get("result_summary","")))
            elif name=="detect_loops":return json.dumps(LoopDetector.detect_loops(_store,args.get("window")))
            elif name=="suggest_breakout":return json.dumps(LoopDetector.suggest_breakout(_store,args.get("loop_id")))
            elif name=="get_action_history":return json.dumps(LoopDetector.get_action_history(_store,args.get("limit",20)))
            elif name=="configure":return json.dumps(LoopDetector.configure(_store,args.get("min_cycle_len"),args.get("max_cycle_len"),args.get("min_repeats"),args.get("window_size")))
            elif name=="get_config":return json.dumps(LoopDetector.get_config(_store))
            elif name=="clear_actions":return json.dumps(LoopDetector.clear_actions(_store))
            elif name=="get_stats":return json.dumps(LoopDetector.get_stats(_store))
            elif name=="reset":return json.dumps(LoopDetector.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPLoopDetectorServer()
    for line in sys.stdin:
        line=line.strip()
        if not line:continue
        try:request=json.loads(line)
        except json.JSONDecodeError:print(json.dumps({"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"}}),flush=True);continue
        method=request.get("method","");req_id=request.get("id");params=request.get("params",{})
        if method=="initialize":response={"jsonrpc":"2.0","id":req_id,"result":{"server":server.name,"version":server.version}}
        elif method=="tools/list":response={"jsonrpc":"2.0","id":req_id,"result":{"tools":server.list_tools()}}
        elif method=="tools/call":
            result=server.handle_tool_call(params.get("name",""),params.get("arguments",{}))
            response={"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":result}]}}
        elif method=="shutdown":response={"jsonrpc":"2.0","id":req_id,"result":{}};print(json.dumps(response),flush=True);break
        else:response={"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Method not found: {method}"}}
        print(json.dumps(response),flush=True)

def main():
    parser=argparse.ArgumentParser(description="MCP Loop Detector Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPLoopDetectorServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
