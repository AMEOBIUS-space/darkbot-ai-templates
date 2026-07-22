# Feature Flag Manager

> Toggles, percentage rollouts, A/B testing, environment targeting, and user overrides

## Features

- 4 flag types: boolean, percentage, variant (A/B), kill_switch
- Deterministic hash-based rollout (same user always gets same result)
- Environment targeting (production, staging, development)
- User targeting (whitelist + blacklist)
- Per-user overrides
- Toggle on/off
- JSON export/import
- Statistics dashboard

## Quick Start

```python
from flags import FeatureFlagManager, FlagType

mgr = FeatureFlagManager(current_environment="production")
mgr.create("new_ui", FlagType.PERCENTAGE, percentage=25.0, description="New UI rollout")
mgr.create("ab_test", FlagType.VARIANT, variants=["control", "treatment"], default_variant="control")

if mgr.is_enabled("new_ui", user_id="user_123"):
    show_new_ui()

variant = mgr.get_variant("ab_test", user_id="user_123")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
