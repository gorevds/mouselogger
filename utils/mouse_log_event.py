class MouseLogEvent:
    def __init__(self, action, x, y, timestamp):
        self.action = action
        self.x = x
        self.y = y
        self.timestamp = timestamp

    def __str__(self):
        return "{0}\t{1}\t{2}\t{3}".format(self.action, self.x, self.y, self.timestamp)

    def __eq__(self, other):
        return self.action == other.action and self.x == other.x and self.y == other.y

    def to_str(self):
        return "{0}\t{1}\t{2}\t{3}\n".format(self.action, self.x, self.y, str(self.timestamp))