"""MCP Server for Eval Harness — agent behavior benchmarks and regression tests."""
import json, sys, argparse
from .eval_harness_engine import EvalHarness

_store = EvalHarness.create_store()

TOOL_DEFS = [
    {"name":"create_suite","description":"Create a test suite with eval criteria.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"description":{"type":"string","default":""},"tests":{"type":"array","items":{"type":"object"}}},"required":["name"]}},
    {"name":"add_test","description":"Add a test case to a suite.","inputSchema":{"type":"object","properties":{"suite_id":{"type":"string"},"test_name":{"type":"string"},"prompt":{"type":"string"},"expected":{"type":"string","default":""},"check_type":{"type":"string","default":"contains"},"max_score":{"type":"integer","default":10}},"required":["suite_id","test_name","prompt"]}},
    {"name":"evaluate_response","description":"Evaluate a single response against expected output.","inputSchema":{"type":"object","properties":{"response":{"type":"string"},"expected":{"type":"string"},"check_type":{"type":"string","default":"contains"}},"required":["response"]}},
    {"name":"run_suite","description":"Run all tests in a suite with provided responses.","inputSchema":{"type":"object","properties":{"suite_id":{"type":"string"},"responses":{"type":"array","items":{"type":"string"}}},"required":["suite_id"]}},
    {"name":"set_baseline","description":"Set current score as regression baseline.","inputSchema":{"type":"object","properties":{"suite_id":{"type":"string"}},"required":["suite_id"]}},
    {"name":"check_regression","description":"Compare latest run against baseline.","inputSchema":{"type":"object","properties":{"suite_id":{"type":"string"}},"required":["suite_id"]}},
    {"name":"get_report","description":"Get eval report for a suite or aggregate.","inputSchema":{"type":"object","properties":{"suite_id":{"type":"string"}},"required":[]}},
    {"name":"list_suites","description":"List all eval suites.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"get_stats","description":"Get eval harness statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all suites, runs, and baselines.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPEvalHarnessServer:
    def __init__(self,name="mcp-eval-harness",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="create_suite":return json.dumps(EvalHarness.create_suite(_store,args["name"],args.get("description",""),args.get("tests")))
            elif name=="add_test":return json.dumps(EvalHarness.add_test(_store,args["suite_id"],args["test_name"],args.get("prompt",""),args.get("expected",""),args.get("check_type","contains"),args.get("max_score",10)))
            elif name=="evaluate_response":return json.dumps(EvalHarness.evaluate_response(_store,args["response"],args.get("expected",""),args.get("check_type","contains")))
            elif name=="run_suite":return json.dumps(EvalHarness.run_suite(_store,args["suite_id"],args.get("responses")))
            elif name=="set_baseline":return json.dumps(EvalHarness.set_baseline(_store,args["suite_id"]))
            elif name=="check_regression":return json.dumps(EvalHarness.check_regression(_store,args["suite_id"]))
            elif name=="get_report":return json.dumps(EvalHarness.get_report(_store,args.get("suite_id")))
            elif name=="list_suites":return json.dumps(EvalHarness.list_suites(_store))
            elif name=="get_stats":return json.dumps(EvalHarness.get_stats(_store))
            elif name=="reset":return json.dumps(EvalHarness.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPEvalHarnessServer()
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
    parser=argparse.ArgumentParser(description="MCP Eval Harness Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPEvalHarnessServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
