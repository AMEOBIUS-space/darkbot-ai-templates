# State Machine

> Finite state machine with transitions, guards, actions, and history

## Features

- State registration with on_enter/on_exit callbacks
- Event-triggered transitions
- Guard conditions (prevent transition if false)
- Transition actions (execute on transition)
- Final states (terminal, no outgoing transitions)
- State history tracking
- Available events listing
- Context dictionary (shared across transitions)
- Event handler side-effects
- Text diagram generator
- Statistics

## Quick Start

```python
from fsm import StateMachine

fsm = StateMachine("idle", context={"credits": 10})
fsm.add_state("idle")
fsm.add_state("running")
fsm.add_state("done", final=True)
fsm.add_transition("idle", "running", "start",
                   guard=lambda ctx: ctx["credits"] > 0,
                   action=lambda ctx: ctx.update({"credits": ctx["credits"] - 1}))
fsm.add_transition("running", "done", "finish")

fsm.trigger("start")
fsm.trigger("finish")
assert fsm.is_final()
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
