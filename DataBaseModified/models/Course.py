import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from persistent import Persistent
import transaction

class Course(persistent.Persistent):
    def __init__(self, id = 0, name = "", professor = 0, file_path = "", curriculum=68, ):
        self.id = id
        self.name = name
        self.professor = professor
        self.file_path = file_path
        self.enrolled_student = []
        self.curriculum=curriculum
        self.quizzes=[]
    
    def get_quizzes(self):
        return self.quizzes

    