"""MCP Server for AB Tester — A/B test prompts, configs, strategies."""
import json, sys, argparse
from .ab_tester_engine import ABTester

_store = ABTester.create_store()

TOOL_DEFS = [
    {"name":"create_experiment","description":"Create a new A/B test experiment.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"description":{"type":"string","default":""},"variants":{"type":"array","items":{"type":"object"}}},"required":["name"]}},
    {"name":"record_trial","description":"Record a trial outcome for a variant.","inputSchema":{"type":"object","properties":{"experiment_id":{"type":"string"},"variant_id":{"type":"string"},"success":{"type":"boolean"},"score":{"type":"number"},"label":{"type":"string","default":""}},"required":["experiment_id","variant_id","success"]}},
    {"name":"get_results","description":"Get experiment results summary.","inputSchema":{"type":"object","properties":{"experiment_id":{"type":"string"}},"required":["experiment_id"]}},
    {"name":"compute_significance","description":"Compute statistical significance between variants.","inputSchema":{"type":"object","properties":{"experiment_id":{"type":"string"}},"required":["experiment_id"]}},
    {"name":"complete_experiment","description":"Mark experiment as completed with winner.","inputSchema":{"type":"object","properties":{"experiment_id":{"type":"string"},"winner":{"type":"string"}},"required":["experiment_id"]}},
    {"name":"list_experiments","description":"List all experiments.","inputSchema":{"type":"object","properties":{"status":{"type":"string"}},"required":[]}},
    {"name":"delete_experiment","description":"Delete an experiment.","inputSchema":{"type":"object","properties":{"experiment_id":{"type":"string"}},"required":["experiment_id"]}},
    {"name":"get_stats","description":"Get A/B testing statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all experiments and trials.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPABTesterServer:
    def __init__(self,name="mcp-ab-tester",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="create_experiment":return json.dumps(ABTester.create_experiment(_store,args["name"],args.get("description",""),args.get("variants")))
            elif name=="record_trial":return json.dumps(ABTester.record_trial(_store,args["experiment_id"],args["variant_id"],args["success"],args.get("score"),args.get("label","")))
            elif name=="get_results":return json.dumps(ABTester.get_results(_store,args["experiment_id"]))
            elif name=="compute_significance":return json.dumps(ABTester.compute_significance(_store,args["experiment_id"]))
            elif name=="complete_experiment":return json.dumps(ABTester.complete_experiment(_store,args["experiment_id"],args.get("winner")))
            elif name=="list_experiments":return json.dumps(ABTester.list_experiments(_store,args.get("status")))
            elif name=="delete_experiment":return json.dumps(ABTester.delete_experiment(_store,args["experiment_id"]))
            elif name=="get_stats":return json.dumps(ABTester.get_stats(_store))
            elif name=="reset":return json.dumps(ABTester.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPABTesterServer()
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
    parser=argparse.ArgumentParser(description="MCP AB Tester Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPABTesterServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
