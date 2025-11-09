import persistent
from persistent.list import PersistentList
import globals
class Course(persistent.Persistent):
    def __init__(self, id = 0, name = "", file_path = "", curriculum=11, ):
        self.id = id
        self.name = name
        self.professor= "Not Assigned"
        self.file_path = file_path
        self.enrolled_student = PersistentList()
        self.curriculum=curriculum
        
    
    def get_quizzes(self):
        quizzes=[]
        for quiz in globals.root["quizzes"]:
            if globals.root["quizzes"][quiz].course_id==self.id:
                quizzes.append(globals.root["quizzes"][quiz])
        return quizzes
                

    
