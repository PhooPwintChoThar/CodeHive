import persistent
from persistent.list import PersistentList
import globals



class Professor(persistent.Persistent):
    def __init__(self, id = 0, name = ""):
        self.id = id
        self.name = name
        self.courses = PersistentList()#course obj

    def get_courses(self):
        return self.courses
    
    def get_quizzes(self):
        
        created_quizzes = []
        for quiz_id in globals.root["quizzes"]:
            if globals.root["quizzes"][quiz_id].professor_id == self.id:
                    created_quizzes.append(globals.root["quizzes"][quiz_id])
        
        
        return created_quizzes
       




        
        

