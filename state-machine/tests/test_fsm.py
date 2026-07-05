import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from fsm import StateMachine, State, Transition


def test_initial_state():
    fsm = StateMachine("idle")
    assert fsm.current_state == "idle"


def test_add_state():
    fsm = StateMachine("idle")
    fsm.add_state("idle")
    fsm.add_state("running")
    assert "idle" in fsm.states
    assert "running" in fsm.states


def test_transition():
    fsm = StateMachine("idle")
    fsm.add_state("idle")
    fsm.add_state("running")
    fsm.add_transition("idle", "running", "start")
    assert fsm.trigger("start") is True
    assert fsm.current_state == "running"


def test_transition_no_match():
    fsm = StateMachine("idle")
    fsm.add_transition("idle", "running", "start")
    assert fsm.trigger("nonexistent") is False
    assert fsm.current_state == "idle"


def test_guard_pass():
    fsm = StateMachine("idle", context={"credits": 10})
    fsm.add_transition("idle", "running", "start",
                       guard=lambda ctx: ctx.get("credits", 0) > 0)
    assert fsm.trigger("start") is True
    assert fsm.current_state == "running"


def test_guard_fail():
    fsm = StateMachine("idle", context={"credits": 0})
    fsm.add_transition("idle", "running", "start",
                       guard=lambda ctx: ctx.get("credits", 0) > 0)
    assert fsm.trigger("start") is False
    assert fsm.current_state == "idle"


def test_action():
    fsm = StateMachine("idle")
    results = []
    fsm.add_transition("idle", "running", "start",
                       action=lambda ctx: results.append("started"))
    fsm.trigger("start")
    assert results == ["started"]


def test_on_enter_exit():
    log = []
    fsm = StateMachine("idle")
    fsm.add_state("idle", on_exit=lambda ctx: log.append("exit_idle"))
    fsm.add_state("running", on_enter=lambda ctx: log.append("enter_running"))
    fsm.add_transition("idle", "running", "start")
    fsm.trigger("start")
    assert log == ["exit_idle", "enter_running"]


def test_final_state():
    fsm = StateMachine("running")
    fsm.add_state("running")
    fsm.add_state("done", final=True)
    fsm.add_transition("running", "done", "finish")
    fsm.trigger("finish")
    assert fsm.is_final() is True
    assert fsm.trigger("anything") is False  # Can't leave final state


def test_history():
    fsm = StateMachine("idle")
    fsm.add_state("idle")
    fsm.add_state("running")
    fsm.add_state("done", final=True)
    fsm.add_transition("idle", "running", "start")
    fsm.add_transition("running", "done", "finish")
    fsm.trigger("start")
    fsm.trigger("finish")
    assert fsm.history == ["idle", "running", "done"]


def test_available_events():
    fsm = StateMachine("idle")
    fsm.add_transition("idle", "running", "start")
    fsm.add_transition("idle", "stopped", "stop")
    events = fsm.available_events()
    assert "start" in events
    assert "stop" in events


def test_can_trigger():
    fsm = StateMachine("idle")
    fsm.add_transition("idle", "running", "start")
    assert fsm.can_trigger("start") is True
    assert fsm.can_trigger("nonexistent") is False


def test_reset():
    fsm = StateMachine("idle")
    fsm.add_state("running")
    fsm.add_transition("idle", "running", "start")
    fsm.trigger("start")
    assert fsm.current_state == "running"
    fsm.reset()
    assert fsm.current_state == "idle"
    assert len(fsm.history) == 1


def test_event_handler():
    fsm = StateMachine("idle")
    events = []
    fsm.on_event("start", lambda ctx: events.append("fired"))
    fsm.add_transition("idle", "running", "start")
    fsm.trigger("start")
    assert events == ["fired"]


def test_diagram():
    fsm = StateMachine("idle")
    fsm.add_state("idle")
    fsm.add_state("running")
    fsm.add_state("done", final=True)
    fsm.add_transition("idle", "running", "start")
    fsm.add_transition("running", "done", "finish")
    diagram = fsm.diagram()
    assert "idle" in diagram
    assert "running" in diagram
    assert "Final" in diagram


def test_stats():
    fsm = StateMachine("idle")
    fsm.add_state("idle")
    fsm.add_state("running")
    fsm.add_transition("idle", "running", "start")
    stats = fsm.stats()
    assert stats["states"] == 2
    assert stats["transitions"] == 1
    assert stats["current_state"] == "idle"


def test_multiple_transitions_same_event():
    fsm = StateMachine("idle")
    fsm.add_transition("idle", "A", "go")
    fsm.add_transition("idle", "B", "go")  # First match wins
    fsm.trigger("go")
    assert fsm.current_state == "A"


def test_context_sharing():
    fsm = StateMachine("idle", context={"counter": 0})
    fsm.add_transition("idle", "idle", "increment",
                       action=lambda ctx: ctx.update({"counter": ctx["counter"] + 1}))
    fsm.trigger("increment")
    fsm.trigger("increment")
    assert fsm.context["counter"] == 2
