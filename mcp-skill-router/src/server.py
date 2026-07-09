"""MCP Server for Skill Router — intent-based task routing to skills."""
import json, sys, argparse
from .skill_router_engine import SkillRouter

_store = SkillRouter.create_store()

TOOL_DEFS = [
    {"name":"register_skill","description":"Register a new skill with keywords and patterns for routing.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"description":{"type":"string"},"keywords":{"type":"array","items":{"type":"string"}},"patterns":{"type":"array","items":{"type":"string"}},"examples":{"type":"array","items":{"type":"string"}},"priority":{"type":"integer","default":0}},"required":["name","description"]}},
    {"name":"route","description":"Route a query to the best matching skills.","inputSchema":{"type":"object","properties":{"query":{"type":"string"},"top_k":{"type":"integer","default":3}},"required":["query"]}},
    {"name":"record_outcome","description":"Record whether a skill routing was successful (for learning).","inputSchema":{"type":"object","properties":{"skill_id":{"type":"string"},"success":{"type":"boolean"}},"required":["skill_id","success"]}},
    {"name":"list_skills","description":"List all registered skills.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"update_skill","description":"Update a registered skill.","inputSchema":{"type":"object","properties":{"skill_id":{"type":"string"},"name":{"type":"string"},"description":{"type":"string"},"keywords":{"type":"array","items":{"type":"string"}},"patterns":{"type":"array","items":{"type":"string"}},"priority":{"type":"integer"}},"required":["skill_id"]}},
    {"name":"remove_skill","description":"Remove a registered skill.","inputSchema":{"type":"object","properties":{"skill_id":{"type":"string"}},"required":["skill_id"]}},
    {"name":"get_routing_history","description":"Get recent routing decisions.","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","default":20}},"required":[]}},
    {"name":"get_stats","description":"Get routing statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all skills and history.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPSkillRouterServer:
    def __init__(self,name="mcp-skill-router",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="register_skill":return json.dumps(SkillRouter.register_skill(_store,args["name"],args["description"],args.get("keywords"),args.get("patterns"),args.get("examples"),args.get("priority",0)))
            elif name=="route":return json.dumps(SkillRouter.route(_store,args["query"],args.get("top_k",3)))
            elif name=="record_outcome":return json.dumps(SkillRouter.record_outcome(_store,args["skill_id"],args["success"]))
            elif name=="list_skills":return json.dumps(SkillRouter.list_skills(_store))
            elif name=="update_skill":return json.dumps(SkillRouter.update_skill(_store,args["skill_id"],args.get("name"),args.get("description"),args.get("keywords"),args.get("patterns"),args.get("priority")))
            elif name=="remove_skill":return json.dumps(SkillRouter.remove_skill(_store,args["skill_id"]))
            elif name=="get_routing_history":return json.dumps(SkillRouter.get_routing_history(_store,args.get("limit",20)))
            elif name=="get_stats":return json.dumps(SkillRouter.get_stats(_store))
            elif name=="reset":return json.dumps(SkillRouter.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPSkillRouterServer()
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
    parser=argparse.ArgumentParser(description="MCP Skill Router Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPSkillRouterServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
