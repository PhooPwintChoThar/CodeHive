import persistent
import bcrypt
import ZODB, ZODB.FileStorage

class Quiz(persistent.Persistent):
    def __init__(self, id = 0, question = "", reference = "", total_s = 5, restriction = ""):
        self.id = id
        self.question = question
        self.reference = reference
        self.total_s = total_s
        self.restriction = restriction
        self.participated_students = []

    def show_student_list(self):
        return self.participated_students
    
    def show_student_result(self, id):
        return self.participated_students[id]

    


