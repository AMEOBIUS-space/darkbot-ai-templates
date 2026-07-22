# AB Testing Framework

> Experiment tracking, variant assignment, and statistical significance testing

## Features

- Experiment lifecycle (draft → running → completed/stopped)
- Deterministic hash-based variant assignment (consistent per user)
- Weight-based traffic splitting (e.g., 80/20)
- Conversion tracking with revenue
- Z-score calculation (two-proportion z-test)
- Statistical significance detection (p < 0.05, 95% confidence)
- Results summary with per-variant metrics
- Multiple experiments support

## Quick Start

```python
from experiment import ABTestingFramework

fw = ABTestingFramework()
fw.create_experiment("button_test", "Button Color Test", variants=["control", "treatment"])
fw.start("button_test")

variant = fw.assign_variant("button_test", user_id="user123")
# Show variant to user...

fw.track_conversion("button_test", user_id="user123", revenue=49.99)

results = fw.results("button_test")
print(f"Significant: {results['is_significant']}")
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
