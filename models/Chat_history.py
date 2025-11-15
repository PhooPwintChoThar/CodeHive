import persistent
from persistent.list import PersistentList
class Chat_history(persistent.Persistent):
    def __init__(self, id = 0):
        self.id = id
        self.messages=PersistentList()
