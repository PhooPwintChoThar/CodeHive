import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction
import BTrees.__OOBTree
from Quiz import Quiz
import random
from Course import Course

storage = ZODB.FileStorage.FileStorage('mydata.fs')
db = ZODB.DB(storage)
connection = db.open()
root = connection.root()

if 'quizzes' not in root:
    root.quizzes = BTrees._OOBTree.BTree()

if 'courses' not in root:
    root.courses = BTrees.__OOBTree.BTree()


quiz_list = root.quizzes
course_list = root.courses

class Professor(persistent.Persistent):
    def __init__(self, id = 0, name = ""):
        self.id = id
        self.name = name
        self.created_quizzes = []
        self.courses = []


    def get_quizzes(self):
        return self.created_quizzes
    
    def create_quiz(self,  question, reference, total_s, restriction):

        id = random.randint(100, 999)
        while id in quiz_list:
            id = random.randint(100, 999)
        quiz = Quiz(id, question, reference, total_s, restriction)

        self.created_quizzes.append(quiz)
    
    def create_course(self, name, file_path):
        
        id = random.randint(100, 999)
        while id in course_list:
            id = random.randint(100, 999)

        course = Course(id, name, self.id, file_path)

        self.courses.append(course)




        
        

