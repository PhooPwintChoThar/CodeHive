import persistent
from persistent import Persistent
import transaction

from models import Discussion
import random
import globals

class Student(persistent.Persistent):
    def __init__(self, id = 0, name = "", batch=68):
        self.id = id
        self.name = name
        self.paticipated_quizzes = []
        self.discussions = []
        self.courses = []
        self.chats = []
        self.batch=batch

    def join_quiz(self, quiz):
        self.paticipated_quizzes.append(quiz)
    
    def create_discussion(self, student, topic, message, timestamp):
        discussion_list=globals.root['discussions']
        id = random.randint(100, 999)
        while id in discussion_list:
            id = random.randint(100, 999)

        discussion = Discussion.Discussion(id, student, topic, message, timestamp)

        self.discussions.append(discussion)
        discussion_list[id]=discussion
        transaction.commit()
    
    def enroll_course(self, course):
        self.courses.append(course)
        course.enrolled_student.append(self.id)




