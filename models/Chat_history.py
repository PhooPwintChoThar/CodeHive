import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction
import BTrees.__OOBTree

class Chat_history(persistent.persistent):
    def __init__(self, id = 0, question = "", answer = ""):
        self.id = id
        self.question = question
        self.answer = answer
        