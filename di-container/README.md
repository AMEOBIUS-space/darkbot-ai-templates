# Dependency Injection Container

> IoC container with singleton, transient, scoped, and factory lifetimes + auto-wiring

## Features

- 4 lifetimes: transient, singleton, scoped, factory
- Auto-wiring (constructor dependency injection via type hints)
- Deep dependency chains (auto-resolves nested dependencies)
- Register existing instances
- Register factory functions
- Tag-based multi-resolution
- Scope management (begin/end)
- Singleton sharing across services
- Singleton clearing (for testing)

## Quick Start

```python
from container import DIContainer, Lifetime

class Logger:
    def log(self, msg): print(msg)

class UserService:
    def __init__(self, logger: Logger):
        self.logger = logger

c = DIContainer()
c.register_singleton(Logger)
c.register(UserService, lifetime=Lifetime.TRANSIENT)

svc = c.resolve(UserService)  # Logger auto-wired
svc.logger.log("Hello!")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
