"""JSON-RPC Server — JSON-RPC 2.0 protocol with method registration and batch support."""
import json
import uuid
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum


class RPCError(Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@dataclass
class RPCRequest:
    jsonrpc: str = "2.0"
    method: str = ""
    params: Any = None
    id: Optional[Union[int, str]] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "RPCRequest":
        if not isinstance(data, dict):
            raise ValueError("Request must be an object")
        if data.get("jsonrpc") != "2.0":
            raise ValueError("Invalid jsonrpc version")
        if "method" not in data:
            raise ValueError("Missing method")
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data["method"],
            params=data.get("params"),
            id=data.get("id"),
        )

    @property
    def is_notification(self) -> bool:
        return self.id is None


@dataclass
class RPCResponse:
    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[Dict] = None
    id: Optional[Union[int, str]] = None

    def to_dict(self) -> Dict:
        d = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class JSONRPCServer:
    """JSON-RPC 2.0 server with method registration and batch support."""

    def __init__(self):
        self.methods: Dict[str, Callable] = {}
        self._middleware: List[Callable] = []

    def register(self, method: str, handler: Callable):
        """Register a method handler."""
        self.methods[method] = handler

    def register_module(self, module: Dict[str, Callable]):
        """Register multiple methods from a dict."""
        for name, handler in module.items():
            self.methods[name] = handler

    def use(self, middleware: Callable):
        """Add middleware (called before method execution)."""
        self._middleware.append(middleware)

    def call(self, method: str, params: Any = None) -> Any:
        """Call a method directly (bypassing JSON parsing)."""
        handler = self.methods.get(method)
        if not handler:
            raise ValueError(f"Method '{method}' not found")
        if isinstance(params, list):
            return handler(*params)
        elif isinstance(params, dict):
            return handler(**params)
        elif params is None:
            return handler()
        else:
            return handler(params)

    def handle(self, request_json: str) -> Optional[str]:
        """Handle a JSON-RPC request string. Returns response JSON or None for notifications."""
        try:
            data = json.loads(request_json)
        except json.JSONDecodeError:
            return RPCResponse(error={"code": RPCError.PARSE_ERROR.value,
                                      "message": "Parse error"}).to_json()

        # Batch request
        if isinstance(data, list):
            if not data:
                return RPCResponse(error={"code": RPCError.INVALID_REQUEST.value,
                                          "message": "Invalid Request"}).to_json()
            responses = []
            for item in data:
                resp = self._handle_single(item)
                if resp is not None:
                    responses.append(resp.to_dict())
            return json.dumps(responses) if responses else None

        # Single request
        response = self._handle_single(data)
        return response.to_json() if response else None

    def _handle_single(self, data: Dict) -> Optional[RPCResponse]:
        """Handle a single request dict."""
        try:
            request = RPCRequest.from_dict(data)
        except ValueError as e:
            return RPCResponse(error={"code": RPCError.INVALID_REQUEST.value,
                                      "message": str(e)})

        # Run middleware
        for mw in self._middleware:
            try:
                mw(request)
            except Exception as e:
                if not request.is_notification:
                    return RPCResponse(
                        error={"code": RPCError.INTERNAL_ERROR.value, "message": str(e)},
                        id=request.id,
                    )
                return None

        # Find method
        handler = self.methods.get(request.method)
        if not handler:
            if not request.is_notification:
                return RPCResponse(
                    error={"code": RPCError.METHOD_NOT_FOUND.value,
                           "message": f"Method '{request.method}' not found"},
                    id=request.id,
                )
            return None

        # Execute
        try:
            if isinstance(request.params, list):
                result = handler(*request.params)
            elif isinstance(request.params, dict):
                result = handler(**request.params)
            elif request.params is None:
                result = handler()
            else:
                result = handler(request.params)

            if request.is_notification:
                return None
            return RPCResponse(result=result, id=request.id)

        except TypeError as e:
            if not request.is_notification:
                return RPCResponse(
                    error={"code": RPCError.INVALID_PARAMS.value, "message": str(e)},
                    id=request.id,
                )
            return None
        except Exception as e:
            if not request.is_notification:
                return RPCResponse(
                    error={"code": RPCError.INTERNAL_ERROR.value, "message": str(e)},
                    id=request.id,
                )
            return None

    def list_methods(self) -> List[str]:
        return list(self.methods.keys())

    def method_exists(self, method: str) -> bool:
        return method in self.methods

    def stats(self) -> Dict:
        return {
            "registered_methods": len(self.methods),
            "middleware_count": len(self._middleware),
        }
