import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from rpc import JSONRPCServer, RPCRequest, RPCResponse, RPCError


def test_register_method():
    server = JSONRPCServer()
    server.register("add", lambda a, b: a + b)
    assert "add" in server.methods


def test_call_method():
    server = JSONRPCServer()
    server.register("add", lambda a, b: a + b)
    assert server.call("add", [2, 3]) == 5


def test_call_named_params():
    server = JSONRPCServer()
    server.register("greet", lambda name: f"Hello, {name}!")
    assert server.call("greet", {"name": "World"}) == "Hello, World!"


def test_call_not_found():
    server = JSONRPCServer()
    try:
        server.call("nonexistent")
        assert False
    except ValueError:
        pass


def test_handle_single_request():
    server = JSONRPCServer()
    server.register("add", lambda a, b: a + b)
    req = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [2, 3], "id": 1})
    resp = server.handle(req)
    data = json.loads(resp)
    assert data["result"] == 5
    assert data["id"] == 1


def test_handle_notification():
    server = JSONRPCServer()
    called = []
    server.register("log", lambda msg: called.append(msg))
    req = json.dumps({"jsonrpc": "2.0", "method": "log", "params": ["hello"]})
    resp = server.handle(req)
    assert resp is None  # Notifications don't get responses
    assert called == ["hello"]


def test_handle_method_not_found():
    server = JSONRPCServer()
    req = json.dumps({"jsonrpc": "2.0", "method": "unknown", "id": 1})
    resp = json.loads(server.handle(req))
    assert resp["error"]["code"] == RPCError.METHOD_NOT_FOUND.value


def test_handle_parse_error():
    server = JSONRPCServer()
    resp = json.loads(server.handle("invalid json"))
    assert resp["error"]["code"] == RPCError.PARSE_ERROR.value


def test_handle_invalid_request():
    server = JSONRPCServer()
    resp = json.loads(server.handle(json.dumps({"foo": "bar"})))
    assert resp["error"]["code"] == RPCError.INVALID_REQUEST.value


def test_handle_batch():
    server = JSONRPCServer()
    server.register("add", lambda a, b: a + b)
    server.register("double", lambda x: x * 2)
    batch = json.dumps([
        {"jsonrpc": "2.0", "method": "add", "params": [1, 2], "id": 1},
        {"jsonrpc": "2.0", "method": "double", "params": [5], "id": 2},
    ])
    resp = json.loads(server.handle(batch))
    assert len(resp) == 2
    assert resp[0]["result"] == 3
    assert resp[1]["result"] == 10


def test_handle_batch_with_notification():
    server = JSONRPCServer()
    called = []
    server.register("log", lambda m: called.append(m))
    server.register("add", lambda a, b: a + b)
    batch = json.dumps([
        {"jsonrpc": "2.0", "method": "log", "params": ["test"]},  # notification
        {"jsonrpc": "2.0", "method": "add", "params": [1, 1], "id": 1},
    ])
    resp = json.loads(server.handle(batch))
    assert len(resp) == 1  # Only the non-notification gets a response
    assert resp[0]["result"] == 2


def test_handle_invalid_params():
    server = JSONRPCServer()
    server.register("add", lambda a, b: a + b)
    req = json.dumps({"jsonrpc": "2.0", "method": "add", "params": [1], "id": 1})
    resp = json.loads(server.handle(req))
    assert resp["error"]["code"] == RPCError.INVALID_PARAMS.value


def test_handle_internal_error():
    server = JSONRPCServer()
    server.register("boom", lambda: 1/0)
    req = json.dumps({"jsonrpc": "2.0", "method": "boom", "id": 1})
    resp = json.loads(server.handle(req))
    assert resp["error"]["code"] == RPCError.INTERNAL_ERROR.value


def test_register_module():
    server = JSONRPCServer()
    server.register_module({"add": lambda a, b: a + b, "sub": lambda a, b: a - b})
    assert "add" in server.methods
    assert "sub" in server.methods


def test_middleware():
    server = JSONRPCServer()
    log = []
    server.use(lambda req: log.append(req.method))
    server.register("test", lambda: "ok")
    server.handle(json.dumps({"jsonrpc": "2.0", "method": "test", "id": 1}))
    assert log == ["test"]


def test_list_methods():
    server = JSONRPCServer()
    server.register("a", lambda: 1)
    server.register("b", lambda: 2)
    assert "a" in server.list_methods()
    assert "b" in server.list_methods()


def test_method_exists():
    server = JSONRPCServer()
    server.register("test", lambda: 1)
    assert server.method_exists("test") is True
    assert server.method_exists("nonexistent") is False


def test_stats():
    server = JSONRPCServer()
    server.register("a", lambda: 1)
    server.use(lambda r: None)
    stats = server.stats()
    assert stats["registered_methods"] == 1
    assert stats["middleware_count"] == 1
