"""Dependency Injection Container — IoC with singleton, factory, and scoped lifetimes."""
from typing import Dict, List, Optional, Callable, Any, Type, TypeVar, Union, get_type_hints
from dataclasses import dataclass, field
from enum import Enum
import inspect


T = TypeVar('T')


class Lifetime(Enum):
    TRANSIENT = "transient"  # New instance every time
    SINGLETON = "singleton"  # One instance for entire app
    SCOPED = "scoped"        # One instance per scope
    FACTORY = "factory"      # Use factory function


@dataclass
class Registration:
    interface: type
    implementation: Union[type, Callable]
    lifetime: Lifetime = Lifetime.TRANSIENT
    instance: Any = None
    factory_args: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class DIContainer:
    """Dependency injection container with auto-wiring."""

    def __init__(self):
        self._registrations: Dict[type, Registration] = {}
        self._singletons: Dict[type, Any] = {}
        self._scoped_instances: Dict[type, Any] = {}
        self._in_scope = False

    def register(self, interface: type, implementation: Union[type, Callable] = None,
                 lifetime: Lifetime = Lifetime.TRANSIENT, tags: List[str] = None) -> Registration:
        """Register a type mapping."""
        impl = implementation or interface
        reg = Registration(interface=interface, implementation=impl,
                           lifetime=lifetime, tags=tags or [])
        self._registrations[interface] = reg
        return reg

    def register_singleton(self, interface: type, implementation: Union[type, Callable] = None) -> Registration:
        return self.register(interface, implementation, Lifetime.SINGLETON)

    def register_factory(self, interface: type, factory: Callable, lifetime: Lifetime = Lifetime.SINGLETON) -> Registration:
        return self.register(interface, factory, lifetime)

    def register_instance(self, interface: type, instance: Any) -> Registration:
        """Register an existing instance as singleton."""
        reg = Registration(interface=interface, implementation=type(instance),
                           lifetime=Lifetime.SINGLETON, instance=instance)
        self._registrations[interface] = reg
        self._singletons[interface] = instance
        return reg

    def resolve(self, interface: type) -> Any:
        """Resolve a dependency."""
        reg = self._registrations.get(interface)
        if not reg:
            # Try to resolve concrete type directly
            if inspect.isclass(interface):
                return self._create_instance(interface)
            raise ValueError(f"Type {interface} not registered")

        # Singleton: return cached instance
        if reg.lifetime == Lifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]
            instance = self._create_from_registration(reg)
            self._singletons[interface] = instance
            return instance

        # Scoped: one per scope
        if reg.lifetime == Lifetime.SCOPED:
            if self._in_scope and interface in self._scoped_instances:
                return self._scoped_instances[interface]
            instance = self._create_from_registration(reg)
            if self._in_scope:
                self._scoped_instances[interface] = instance
            return instance

        # Transient or Factory: always new
        return self._create_from_registration(reg)

    def _create_from_registration(self, reg: Registration) -> Any:
        if reg.instance is not None:
            return reg.instance
        return self._create_instance(reg.implementation)

    def _create_instance(self, cls_or_factory: Union[type, Callable]) -> Any:
        """Create instance with auto-wired dependencies."""
        if callable(cls_or_factory) and not inspect.isclass(cls_or_factory):
            # Factory function
            return self._call_with_dependencies(cls_or_factory)

        # Class: inspect constructor
        sig = inspect.signature(cls_or_factory.__init__)
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.resolve(param.annotation)
                except ValueError:
                    if param.default != inspect.Parameter.empty:
                        pass  # Use default
                    else:
                        raise
            elif param.default != inspect.Parameter.empty:
                pass  # Use default
        return cls_or_factory(**kwargs)

    def _call_with_dependencies(self, func: Callable) -> Any:
        """Call a function with auto-wired dependencies."""
        sig = inspect.signature(func)
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.resolve(param.annotation)
                except ValueError:
                    if param.default == inspect.Parameter.empty:
                        raise
        return func(**kwargs)

    def resolve_all(self, tag: str) -> List[Any]:
        """Resolve all registrations with a given tag."""
        results = []
        for interface, reg in self._registrations.items():
            if tag in reg.tags:
                results.append(self.resolve(interface))
        return results

    def is_registered(self, interface: type) -> bool:
        return interface in self._registrations

    def begin_scope(self):
        """Begin a new scope."""
        self._in_scope = True
        self._scoped_instances = {}

    def end_scope(self):
        """End the current scope."""
        self._in_scope = False
        self._scoped_instances = {}

    def clear_singletons(self):
        """Clear all singleton instances (useful for testing)."""
        self._singletons = {}

    def list_registrations(self) -> List[Dict]:
        return [
            {"interface": str(r.interface), "implementation": str(r.implementation),
             "lifetime": r.lifetime.value, "tags": r.tags}
            for r in self._registrations.values()
        ]

    def stats(self) -> Dict:
        return {
            "registrations": len(self._registrations),
            "singletons": len(self._singletons),
            "in_scope": self._in_scope,
        }
