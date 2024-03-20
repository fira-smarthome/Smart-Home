class FiraWindowSender:
    def __init__(self, supervisor):
        self.history = []
        self.supervisor = supervisor

    def update_history(self, command: str, args: str = ''):
        self.history.append([command, args])

    def send(self, command: str, args: str = ''):
        self.supervisor.wwiSendText(command + ',' + args)
        self.update_history(command, args)

    def send_all(self):
        for command, args in self.history:
            self.supervisor.wwiSendText(command + ',' + args)
