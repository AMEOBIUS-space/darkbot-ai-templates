"""MCP Server for Token Budget — cost tracking, budgets, optimization."""
import json, sys, argparse
from .token_budget_engine import TokenBudget

_store = TokenBudget.create_store()

TOOL_DEFS = [
    {"name":"estimate_tokens","description":"Estimate token count for text.","inputSchema":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}},
    {"name":"estimate_cost","description":"Estimate cost for a model call.","inputSchema":{"type":"object","properties":{"model":{"type":"string"},"input_tokens":{"type":"integer"},"output_tokens":{"type":"integer"}},"required":["model","input_tokens","output_tokens"]}},
    {"name":"log_usage","description":"Log actual token usage with cost tracking.","inputSchema":{"type":"object","properties":{"model":{"type":"string"},"input_tokens":{"type":"integer"},"output_tokens":{"type":"integer"},"label":{"type":"string","default":""}},"required":["model","input_tokens","output_tokens"]}},
    {"name":"set_budget","description":"Set a spending budget in USD.","inputSchema":{"type":"object","properties":{"limit_usd":{"type":"number"}},"required":["limit_usd"]}},
    {"name":"get_budget_status","description":"Check budget usage and remaining.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"get_usage_report","description":"Get usage report by model or label.","inputSchema":{"type":"object","properties":{"by":{"type":"string","default":"model"}},"required":[]}},
    {"name":"list_models","description":"List supported models with pricing.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"optimize","description":"Compare costs across models for given tokens.","inputSchema":{"type":"object","properties":{"input_tokens":{"type":"integer"},"output_tokens":{"type":"integer"},"models":{"type":"array","items":{"type":"string"}}},"required":["input_tokens","output_tokens"]}},
    {"name":"get_alerts","description":"Get budget alerts history.","inputSchema":{"type":"object","properties":{"limit":{"type":"integer","default":10}},"required":[]}},
    {"name":"get_stats","description":"Get aggregate statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all usage data and budgets.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPTokenBudgetServer:
    def __init__(self,name="mcp-token-budget",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="estimate_tokens":return json.dumps({"success":True,"tokens":TokenBudget.estimate_tokens(args["text"]),"text_length":len(args["text"])})
            elif name=="estimate_cost":return json.dumps(TokenBudget.estimate_cost(args["model"],args["input_tokens"],args["output_tokens"]))
            elif name=="log_usage":return json.dumps(TokenBudget.log_usage(_store,args["model"],args["input_tokens"],args["output_tokens"],args.get("label","")))
            elif name=="set_budget":return json.dumps(TokenBudget.set_budget(_store,args["limit_usd"]))
            elif name=="get_budget_status":return json.dumps(TokenBudget.get_budget_status(_store))
            elif name=="get_usage_report":return json.dumps(TokenBudget.get_usage_report(_store,args.get("by","model")))
            elif name=="list_models":return json.dumps(TokenBudget.list_models(_store))
            elif name=="optimize":return json.dumps(TokenBudget.optimize(_store,args["input_tokens"],args["output_tokens"],args.get("models")))
            elif name=="get_alerts":return json.dumps(TokenBudget.get_alerts(_store,args.get("limit",10)))
            elif name=="get_stats":return json.dumps(TokenBudget.get_stats(_store))
            elif name=="reset":return json.dumps(TokenBudget.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPTokenBudgetServer()
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
    parser=argparse.ArgumentParser(description="MCP Token Budget Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPTokenBudgetServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
