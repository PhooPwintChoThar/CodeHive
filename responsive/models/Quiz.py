import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from datetime import date
class Quiz(persistent.Persistent):
    def __init__(self, id = 0,title="Quiz", question = "", sample_sol = "",  duedate=date, duration=15,restriction = "", total_s = 5):
        self.id = id
        self.title=title
        self.question = question
        self.sample_sol = sample_sol
        self.total_s = total_s
        self.restriction = restriction
        self.participated_students = []
        self.duedate=duedate
        self.duration=duration
        

    def show_student_list(self):
        return self.participated_students
    
    def show_student_result(self, id):
        return self.participated_students[id]

    


