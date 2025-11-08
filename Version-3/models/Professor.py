import persistent
from persistent import Persistent
from models.Quiz import Quiz
import random
from models.Course import Course
import globals
import transaction


class Professor(persistent.Persistent):
    def __init__(self, id = 0, name = ""):
        self.id = id
        self.name = name
        self.courses = []

    def get_courses(self):
        return self.courses
    
    def get_quizzes(self):
        
        created_quizzes = []
        for quiz_id in globals.root["quizzes"]:
            if globals.root["quizzes"][quiz_id].professor_id == self.id:
                    created_quizzes.append(globals.root["quizzes"][quiz_id])
        
        
        return created_quizzes
       




        
        

