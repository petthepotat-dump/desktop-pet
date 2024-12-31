class SignalHandler:

    SIGNAL_QUEUE = []
    SIGNAL_RECEIVERS = {}

    @classmethod
    def iterate_signals(cls):
        # print(cls.SIGNAL_QUEUE)
        for signal in cls.SIGNAL_QUEUE:
            receiver, args = signal
            if receiver in cls.SIGNAL_RECEIVERS:
                for function in cls.SIGNAL_RECEIVERS[receiver]:
                    function(args)
        cls.SIGNAL_QUEUE = []

    @classmethod
    def add_receiver(cls, receiver: str, function: "function"):
        if receiver not in cls.SIGNAL_RECEIVERS:
            cls.SIGNAL_RECEIVERS[receiver] = []
        cls.SIGNAL_RECEIVERS[receiver].append(function)

    @classmethod
    def add_signal(cls, receiver: str, args: dict):
        # print(f"Adding signal {receiver} with args {args}")
        cls.SIGNAL_QUEUE.append((receiver, args))
