import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction
import BTrees.__OOBTree

class Course(persistent.persistent):
    def __init__(self, id = 0, name = "", professor = 0, file_path = ""):
        self.id = id
        self.name = name
        self.professor = professor
        self.file_path = file_path
        self.enrolled_student = []

    