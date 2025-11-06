import persistent
from persistent import Persistent
from models.Quiz import Quiz
import random
from models.Course import Course
import globals


class Professor(persistent.Persistent):
    def __init__(self, id = 0, name = ""):
        self.id = id
        self.name = name
        self.created_quizzes = []
        self.courses = []


    def get_quizzes(self):
        return self.created_quizzes
    
    def create_quiz(self,  question, reference, total_s, restriction):
        quiz_list = globals.root["quizzes"]

        id = random.randint(100, 999)
        while id in quiz_list:
            id = random.randint(100, 999)
        quiz = Quiz(id, question, reference, total_s, restriction)

        self.created_quizzes.append(quiz)
        quiz_list[id]=quiz
        
    
    def create_course(self, name, file_path):
        course_list=globals.root["courses"]
        id = random.randint(100, 999)
        while id in course_list:
            id = random.randint(100, 999)

        course = Course(id, name, self.id, file_path)

        self.courses.append(course)
        course_list[id]=course
       




        
        

