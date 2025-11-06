import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from persistent import Persistent
import transaction

class Course(persistent.Persistent):
    def __init__(self, id = 0, name = "", professor = 0, file_path = ""):
        self.id = id
        self.name = name
        self.professor = professor
        self.file_path = file_path
        self.enrolled_student = []

    