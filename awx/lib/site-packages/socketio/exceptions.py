class SessionNotFound(Exception):
    def __init__(self, sessid):
        self.sessid = sessid

    def __str__(self):
        return "Session %s not found!" % self.sessid
