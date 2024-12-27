import pygame


# ---------------------------- #
# constants

COMPONENT_NAME = "StateMachineComponent"

# ---------------------------- #
# component


class StateMachineComponent:

    def __init__(self):
        """Initialize the renderable component"""
        super().__init__()

        self._states = {}
        self._next_state: str = None
        self._current_state: str = None

    # ---------------------------- #
    # logic

    def set_next_state(self, name: str):
        """Set the next state"""
        self._next_state = self.get_state(name)

    def set_current_state(self, name: str):
        """Set the current state"""
        self._current_state = self.get_state(name)

    def get_current_state(self) -> "State":
        """Get the current state"""
        return self._current_state

    def add_state(self, state: "State"):
        """Add a state to the state machine"""
        self._states[state.get_name()] = state
        state.__post_init__(self)

    def get_state(self, name: str) -> "State":
        """Get a state by name"""
        return self._states.get(name, None)

    def remove_state(self, name: str):
        """Remove a state by name"""
        return self._states.pop(name, None)

    def update(self):
        if not self.get_current_state():
            return

        # run statemachine logic
        if self._next_state != None:
            self.get_current_state().on_exit()
            self._current_state = self._next_state
            self.get_current_state().on_enter()
            self._next_state = None

        # update state
        self.get_current_state().update()


class State:
    def __init__(self, name: str):
        self._name = name
        self._statemachine = None

    def __post_init__(self, statemachine: "StateMachineComponent"):
        self._statemachine = statemachine

    # ---------------------------- #
    # logic

    def on_enter(self):
        """Called when the state is entered"""
        pass

    def on_exit(self):
        """Called when the state is exited"""
        pass

    def update(self):
        """Update the state"""
        pass

    # ---------------------------- #
    # utils

    def get_name(self) -> str:
        return self._name

    def get_statemachine(self) -> "StateMachineComponent":
        return self._statemachine
