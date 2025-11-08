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
        created_quizzes=[]
        if self.courses:
            for c in self.courses:
                created_quizzes+=c.get_quizzes()
        return created_quizzes
    
    def create_quiz(self, course, title, question, sample_output, duedate, duration, restriction, total_s):
        quiz_list = globals.root["quizzes"]
        course=globals.root["courses"][course]
       

        id = random.randint(100, 999)
        while id in quiz_list:
            id = random.randint(100, 999)
        quiz = Quiz(id, title, question,  sample_output, duedate, duration, restriction, total_s)
        course.quizzes.append(quiz)
        quiz_list[id]=quiz
        transaction.commit()

        
    
    def create_course(self, name, file_path, curriculum):
        course_list=globals.root["courses"]
        id = random.randint(100, 999)
        while id in course_list:
            id = random.randint(100, 999)

        course = Course(id, name, self.id, file_path, curriculum)

        self.courses.append(course)
        course_list[id]=course
        transaction.commit()
       




        
        

