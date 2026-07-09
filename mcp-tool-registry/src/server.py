"""MCP Server for Tool Registry — dynamic tool management."""
import json, sys, argparse
from .tool_registry_engine import ToolRegistry

_store = ToolRegistry.create_store()

TOOL_DEFS = [
    {"name":"register","description":"Register a new tool in the registry.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"description":{"type":"string","default":""},"schema":{"type":"object"},"category":{"type":"string","default":"general"},"version":{"type":"string","default":"1.0.0"},"tags":{"type":"array","items":{"type":"string"}}},"required":["name"]}},
    {"name":"unregister","description":"Remove a tool from the registry.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}},
    {"name":"enable","description":"Enable a registered tool.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}},
    {"name":"disable","description":"Disable a registered tool.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}},
    {"name":"record_call","description":"Record a tool call outcome.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"success":{"type":"boolean"},"latency_ms":{"type":"number","default":0}},"required":["name","success"]}},
    {"name":"get_tool","description":"Get details of a registered tool.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}},
    {"name":"list_tools","description":"List registered tools, optionally filtered.","inputSchema":{"type":"object","properties":{"category":{"type":"string"},"enabled_only":{"type":"boolean","default":False}},"required":[]}},
    {"name":"search","description":"Search tools by name, description, or tag.","inputSchema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}},
    {"name":"health_check","description":"Check health of one or all tools.","inputSchema":{"type":"object","properties":{"name":{"type":"string"}},"required":[]}},
    {"name":"get_categories","description":"List all tool categories.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"get_stats","description":"Get registry statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset the entire registry.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPToolRegistryServer:
    def __init__(self,name="mcp-tool-registry",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="register":return json.dumps(ToolRegistry.register(_store,args["name"],args.get("description",""),args.get("schema"),args.get("category","general"),args.get("version","1.0.0"),args.get("tags")))
            elif name=="unregister":return json.dumps(ToolRegistry.unregister(_store,args["name"]))
            elif name=="enable":return json.dumps(ToolRegistry.enable(_store,args["name"]))
            elif name=="disable":return json.dumps(ToolRegistry.disable(_store,args["name"]))
            elif name=="record_call":return json.dumps(ToolRegistry.record_call(_store,args["name"],args["success"],args.get("latency_ms",0)))
            elif name=="get_tool":return json.dumps(ToolRegistry.get_tool(_store,args["name"]))
            elif name=="list_tools":return json.dumps(ToolRegistry.list_tools(_store,args.get("category"),args.get("enabled_only",False)))
            elif name=="search":return json.dumps(ToolRegistry.search(_store,args["query"]))
            elif name=="health_check":return json.dumps(ToolRegistry.health_check(_store,args.get("name")))
            elif name=="get_categories":return json.dumps(ToolRegistry.get_categories(_store))
            elif name=="get_stats":return json.dumps(ToolRegistry.get_stats(_store))
            elif name=="reset":return json.dumps(ToolRegistry.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPToolRegistryServer()
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
    parser=argparse.ArgumentParser(description="MCP Tool Registry Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPToolRegistryServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
