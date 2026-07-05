"""State Machine — finite state machine with transitions, guards, and actions."""
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Transition:
    from_state: str
    to_state: str
    event: str
    guard: Optional[Callable[[Dict], bool]] = None
    action: Optional[Callable[[Dict], None]] = None
    description: str = ""


@dataclass
class State:
    name: str
    on_enter: Optional[Callable[[Dict], None]] = None
    on_exit: Optional[Callable[[Dict], None]] = None
    final: bool = False


class StateMachine:
    """Finite state machine with transitions, guards, and actions."""

    def __init__(self, initial_state: str, context: Dict = None):
        self.states: Dict[str, State] = {}
        self.transitions: List[Transition] = []
        self.current_state: str = initial_state
        self.context: Dict = context or {}
        self.history: List[str] = [initial_state]
        self._event_handlers: Dict[str, List[Callable]] = {}

    def add_state(self, name: str, on_enter: Callable = None,
                  on_exit: Callable = None, final: bool = False) -> State:
        state = State(name=name, on_enter=on_enter, on_exit=on_exit, final=final)
        self.states[name] = state
        return state

    def add_transition(self, from_state: str, to_state: str, event: str,
                       guard: Callable = None, action: Callable = None,
                       description: str = "") -> Transition:
        trans = Transition(from_state=from_state, to_state=to_state, event=event,
                           guard=guard, action=action, description=description)
        self.transitions.append(trans)
        return trans

    def on_event(self, event: str, handler: Callable):
        """Register a side-effect handler for an event."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def trigger(self, event: str) -> bool:
        """Trigger an event. Returns True if transition occurred."""
        if self.is_final():
            return False

        for trans in self.transitions:
            if trans.from_state == self.current_state and trans.event == event:
                # Check guard
                if trans.guard and not trans.guard(self.context):
                    return False

                # Execute exit action
                old_state = self.states.get(self.current_state)
                if old_state and old_state.on_exit:
                    old_state.on_exit(self.context)

                # Execute transition action
                if trans.action:
                    trans.action(self.context)

                # Change state
                self.current_state = trans.to_state
                self.history.append(self.current_state)

                # Execute enter action
                new_state = self.states.get(self.current_state)
                if new_state and new_state.on_enter:
                    new_state.on_enter(self.context)

                # Fire event handlers
                for handler in self._event_handlers.get(event, []):
                    try:
                        handler(self.context)
                    except Exception:
                        pass

                return True
        return False

    def can_trigger(self, event: str) -> bool:
        """Check if an event can be triggered from current state."""
        if self.is_final():
            return False
        for trans in self.transitions:
            if trans.from_state == self.current_state and trans.event == event:
                if trans.guard and not trans.guard(self.context):
                    return False
                return True
        return False

    def is_final(self) -> bool:
        state = self.states.get(self.current_state)
        return state.final if state else False

    def available_events(self) -> List[str]:
        """Get list of events that can be triggered from current state."""
        return [t.event for t in self.transitions
                if t.from_state == self.current_state
                and (not t.guard or t.guard(self.context))]

    def reset(self, initial_state: str = None):
        """Reset to initial state."""
        self.current_state = initial_state or self.history[0]
        self.history = [self.current_state]
        self.context = {}

    def diagram(self) -> str:
        """Generate a simple text diagram of the state machine."""
        lines = []
        for trans in self.transitions:
            guard_str = " [guard]" if trans.guard else ""
            lines.append(f"  {trans.from_state} --({trans.event}{guard_str})--> {trans.to_state}")
        final_states = [s for s in self.states.values() if s.final]
        if final_states:
            lines.append(f"  Final: {', '.join(s.name for s in final_states)}")
        return "\n".join(lines)

    def stats(self) -> Dict:
        return {
            "states": len(self.states),
            "transitions": len(self.transitions),
            "current_state": self.current_state,
            "history_length": len(self.history),
            "is_final": self.is_final(),
            "available_events": self.available_events(),
        }
