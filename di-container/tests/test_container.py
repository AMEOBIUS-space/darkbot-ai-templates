import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from container import DIContainer, Lifetime


class Logger:
    def __init__(self):
        self.messages = []
    def log(self, msg):
        self.messages.append(msg)

class Database:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.data = {}

class UserService:
    def __init__(self, db: Database, logger: Logger):
        self.db = db
        self.logger = logger


def test_register_resolve():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    instance = c.resolve(Logger)
    assert isinstance(instance, Logger)


def test_singleton_same_instance():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    a = c.resolve(Logger)
    b = c.resolve(Logger)
    assert a is b


def test_transient_different_instances():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.TRANSIENT)
    a = c.resolve(Logger)
    b = c.resolve(Logger)
    assert a is not b


def test_auto_wiring():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    c.register(Database, Database, Lifetime.SINGLETON)
    db = c.resolve(Database)
    assert isinstance(db, Database)
    assert isinstance(db.logger, Logger)


def test_deep_wiring():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    c.register(Database, Database, Lifetime.SINGLETON)
    c.register(UserService, UserService, Lifetime.TRANSIENT)
    svc = c.resolve(UserService)
    assert isinstance(svc, UserService)
    assert isinstance(svc.db, Database)
    assert isinstance(svc.logger, Logger)


def test_register_instance():
    c = DIContainer()
    logger = Logger()
    c.register_instance(Logger, logger)
    assert c.resolve(Logger) is logger


def test_register_factory():
    c = DIContainer()
    c.register_factory(Logger, lambda: Logger(), Lifetime.SINGLETON)
    instance = c.resolve(Logger)
    assert isinstance(instance, Logger)


def test_scoped():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SCOPED)
    c.begin_scope()
    a = c.resolve(Logger)
    b = c.resolve(Logger)
    assert a is b  # Same within scope
    c.end_scope()
    c.begin_scope()
    d = c.resolve(Logger)
    assert d is not a  # Different across scopes
    c.end_scope()


def test_not_registered():
    from typing import Protocol
    class MyService(Protocol):
        def do(self) -> None: pass
    c = DIContainer()
    try:
        c.resolve(MyService)
        assert False
    except (ValueError, TypeError):
        pass


def test_is_registered():
    c = DIContainer()
    c.register(Logger, Logger)
    assert c.is_registered(Logger) is True
    assert c.is_registered(Database) is False


def test_resolve_all_by_tag():
    c = DIContainer()
    c.register(Logger, Logger, tags=["plugin"])
    c.register(Database, Database, tags=["plugin"])
    instances = c.resolve_all("plugin")
    assert len(instances) == 2


def test_clear_singletons():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    a = c.resolve(Logger)
    c.clear_singletons()
    b = c.resolve(Logger)
    assert a is not b


def test_list_registrations():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    c.register(Database, Database, Lifetime.TRANSIENT)
    regs = c.list_registrations()
    assert len(regs) == 2
    assert regs[0]["lifetime"] == "singleton"


def test_stats():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    c.resolve(Logger)  # Create singleton
    stats = c.stats()
    assert stats["registrations"] == 1
    assert stats["singletons"] == 1


def test_singleton_sharing():
    c = DIContainer()
    c.register(Logger, Logger, Lifetime.SINGLETON)
    c.register(Database, Database, Lifetime.SINGLETON)
    c.register(UserService, UserService, Lifetime.TRANSIENT)
    svc1 = c.resolve(UserService)
    svc2 = c.resolve(UserService)
    assert svc1 is not svc2  # Different transient instances
    assert svc1.logger is svc2.logger  # But same singleton logger


def test_register_singleton_helper():
    c = DIContainer()
    c.register_singleton(Logger, Logger)
    a = c.resolve(Logger)
    b = c.resolve(Logger)
    assert a is b
