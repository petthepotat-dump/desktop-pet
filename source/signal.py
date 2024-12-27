class SignalHandler:

    SIGNAL_QUEUE = []

    def iterate_signals(self):
        for signal in self.SIGNAL_QUEUE:
            signal.execute()
        self.SIGNAL_QUEUE = []


class Signal:
    def __init__(self, handler: SignalHandler):
        self.handler = handler

    def execute(self):
        pass
