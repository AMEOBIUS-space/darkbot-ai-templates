# State Machine: Finite State Automation Without Dependencies

> Part of the [darkbot-templates](https://github.com/AMEOBIUS-space/darkbot-ai-templates) series — zero-dependency production templates.

Every non-trivial system has states: orders go pending → paid → shipped → delivered. Bot conversations flow menu → input → confirm → done. Hand-rolled `if/else` ladders break. A finite state machine makes transitions explicit, guarded, and debuggable.

## Usage

```python
from darkbot_templates.templates.state_machine import StateMachine

sm = StateMachine("order", initial="pending")
sm.add_state("pending")
sm.add_state("paid")
sm.add_state("shipped")
sm.add_state("delivered")
sm.add_state("cancelled")

sm.add_transition("pending", "paid", "PAYMENT_RECEIVED")
sm.add_transition("paid", "shipped", "SHIP")
sm.add_transition("shipped", "delivered", "DELIVER")
sm.add_transition("pending", "cancelled", "CANCEL")
sm.add_transition("paid", "cancelled", "REFUND")

sm.start()
print(sm.current_state)  # "pending"

sm.send("PAYMENT_RECEIVED")
print(sm.current_state)  # "paid"

sm.send("SHIP")
print(sm.current_state)  # "shipped"
```

## Guards and Actions

Transitions can have **guards** (conditional execution) and **actions** (side effects):

```python
def inventory_available():
    return check_stock() > 0

def reserve_items(transition):
    decrement_stock()

sm.add_transition(
    "paid", "shipped", "SHIP",
    guard=inventory_available,    # only ship if stock exists
    action=reserve_items,         # decrement on transition
)
```

If `inventory_available()` returns `False`, the transition is blocked — `send("SHIP")` returns `False` and the state stays `paid`.

## Entry/Exit Callbacks

```python
def notify_customer(state):
    send_email(f"Your order is now {state.name}")

sm.add_state("shipped", on_enter=notify_customer)
sm.add_state("delivered", on_enter=notify_customer)
```

Callbacks fire on state entry and exit — useful for notifications, logging, metrics.

## History and Debugging

```python
sm = StateMachine("bot", initial="menu", history_size=50)

# ... run transitions ...

for entry in sm.history:
    print(f"  {entry['timestamp']:.0f}  {entry['from']} → {entry['to']}  ({entry['event']})")
```

The history log records every transition with timestamp — invaluable for debugging "how did we get here?" questions.

## Telegram Bot Conversation Flow

```python
sm = StateMachine("tgbot", initial="start")
sm.add_state("start")
sm.add_state("await_phone")
sm.add_state("await_code")
sm.add_state("logged_in")

sm.add_transition("start", "await_phone", "LOGIN")
sm.add_transition("await_phone", "await_code", "PHONE_SUBMITTED")
sm.add_transition("await_code", "logged_in", "CODE_VERIFIED")
sm.add_transition("await_code", "await_phone", "RETRY")

def handle_update(update):
    event = parse_event(update, sm.current_state)
    sm.send(event)
    return render_response(sm.current_state)
```

## DOT Graph Export

```python
dot = sm.to_dot()
# digraph "order" {
#   pending -> paid [label="PAYMENT_RECEIVED"];
#   paid -> shipped [label="SHIP"];
#   ...
# }
```

Paste into [GraphvizOnline](https://dreampuf.github.io/GraphvizOnline/) for instant visualization.

## Testing

```bash
pytest tests/test_state_machine.py -v
```

## References

- [UML State Machines](https://www.uml-diagrams.org/state-machine-diagrams.html)
- [XState (JS)](https://xstate.js.org/docs/) — inspiration for guarded transitions

---

*darkbot-templates v1.8.5 — 30 templates, zero dependencies, 448 tests.*
