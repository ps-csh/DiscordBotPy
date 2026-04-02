class Event:
    listeners = []

    def __init__(self):
        pass

    def register_listener(self, listener: function):
        self.listeners.append(listener)

    def unregister_listener(self, listener: function):
        self.listeners.remove(listener)

    def invoke(self, data: any):
        for listener in self.listeners:
            listener(data)