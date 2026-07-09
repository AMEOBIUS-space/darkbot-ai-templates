"""MCP Server for Prompt Versioning — save, diff, rollback, branch prompts."""
import json, sys, argparse
from .prompt_versioning_engine import PromptVersioning

_store = PromptVersioning.create_store()

TOOL_DEFS = [
    {"name":"create_prompt","description":"Create a new versioned prompt.","inputSchema":{"type":"object","properties":{"name":{"type":"string"},"text":{"type":"string"},"metadata":{"type":"object"}},"required":["name","text"]}},
    {"name":"save_version","description":"Save a new version of an existing prompt.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"},"text":{"type":"string"},"metadata":{"type":"object"},"message":{"type":"string","default":""}},"required":["prompt_id","text"]}},
    {"name":"get_version","description":"Get a specific version of a prompt.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"},"version_id":{"type":"string"}},"required":["prompt_id"]}},
    {"name":"get_active","description":"Get the active version of a prompt.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"}},"required":["prompt_id"]}},
    {"name":"rollback","description":"Roll back active version to a previous one.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"},"version_id":{"type":"string"}},"required":["prompt_id","version_id"]}},
    {"name":"diff","description":"Diff two versions of a prompt.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"},"version_a":{"type":"string"},"version_b":{"type":"string"}},"required":["prompt_id","version_a","version_b"]}},
    {"name":"list_versions","description":"List all versions of a prompt.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"}},"required":["prompt_id"]}},
    {"name":"list_prompts","description":"List all versioned prompts.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"branch","description":"Create a branch from a version.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"},"branch_name":{"type":"string"},"from_version":{"type":"string"}},"required":["prompt_id","branch_name"]}},
    {"name":"compare_effectiveness","description":"Compare two versions with effectiveness scores.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"},"version_a":{"type":"string"},"version_b":{"type":"string"},"score_a":{"type":"number"},"score_b":{"type":"number"}},"required":["prompt_id","version_a","version_b","score_a","score_b"]}},
    {"name":"delete_prompt","description":"Delete a prompt and all its versions.","inputSchema":{"type":"object","properties":{"prompt_id":{"type":"string"}},"required":["prompt_id"]}},
    {"name":"get_stats","description":"Get versioning statistics.","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"reset","description":"Reset all prompts and versions.","inputSchema":{"type":"object","properties":{},"required":[]}},
]

class MCPPromptVersioningServer:
    def __init__(self,name="mcp-prompt-versioning",version="1.0.0"):
        self.name=name;self.version=version
    def list_tools(self):return TOOL_DEFS
    def manifest(self):return{"server":{"name":self.name,"version":self.version},"capabilities":{"tools":{"listChanged":False}},"tools":self.list_tools()}
    def handle_tool_call(self,name,args):
        try:
            if name=="create_prompt":return json.dumps(PromptVersioning.create_prompt(_store,args["name"],args["text"],args.get("metadata")))
            elif name=="save_version":return json.dumps(PromptVersioning.save_version(_store,args["prompt_id"],args["text"],args.get("metadata"),args.get("message","")))
            elif name=="get_version":return json.dumps(PromptVersioning.get_version(_store,args["prompt_id"],args.get("version_id")))
            elif name=="get_active":return json.dumps(PromptVersioning.get_active(_store,args["prompt_id"]))
            elif name=="rollback":return json.dumps(PromptVersioning.rollback(_store,args["prompt_id"],args["version_id"]))
            elif name=="diff":return json.dumps(PromptVersioning.diff(_store,args["prompt_id"],args["version_a"],args["version_b"]))
            elif name=="list_versions":return json.dumps(PromptVersioning.list_versions(_store,args["prompt_id"]))
            elif name=="list_prompts":return json.dumps(PromptVersioning.list_prompts(_store))
            elif name=="branch":return json.dumps(PromptVersioning.branch(_store,args["prompt_id"],args["branch_name"],args.get("from_version")))
            elif name=="compare_effectiveness":return json.dumps(PromptVersioning.compare_effectiveness(_store,args["prompt_id"],args["version_a"],args["version_b"],args["score_a"],args["score_b"]))
            elif name=="delete_prompt":return json.dumps(PromptVersioning.delete_prompt(_store,args["prompt_id"]))
            elif name=="get_stats":return json.dumps(PromptVersioning.get_stats(_store))
            elif name=="reset":return json.dumps(PromptVersioning.reset(_store))
            else:return json.dumps({"error":f"Unknown tool: {name}"})
        except KeyError as e:return json.dumps({"error":f"Missing required parameter: {e}","tool":name})
        except Exception as e:return json.dumps({"error":str(e),"tool":name})

def _run_stdio():
    server=MCPPromptVersioningServer()
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
    parser=argparse.ArgumentParser(description="MCP Prompt Versioning Server")
    parser.add_argument("--stdio",action="store_true")
    parser.add_argument("--manifest",action="store_true")
    args=parser.parse_args()
    if args.manifest:print(json.dumps(MCPPromptVersioningServer().manifest(),indent=2))
    elif args.stdio:_run_stdio()
    else:parser.print_help()

if __name__=="__main__":main()
