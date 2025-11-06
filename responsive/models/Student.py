import persistent
import bcrypt
import ZODB, ZODB.FileStorage
from BTrees.OOBTree import OOBTree
from persistent import Persistent
import transaction
import BTrees.__OOBTree
from Discussion import Discussion
import random
from Course import Course


storage = ZODB.FileStorage.FileStorage('mydata.fs')
db = ZODB.DB(storage)
connection = db.open()
root = connection.root()

if 'discussions' not in root:
    root.discussions = BTrees._OOBTree.BTree()

discussion_list = root.discussions

class Student(persistent.persistent):
    def __init__(self, id = 0, name = ""):
        self.id = id
        self.name = name
        self.paticipated_quizzes = []
        self.discussions = []
        self.courses = []
        self.chats = []

    def join_quiz(self, quiz):
        self.paticipated_quizzes.append(quiz)
    
    def create_discussion(self, student, topic, message, timestamp):

        id = random.randint(100, 999)
        while id in discussion_list:
            id = random.randint(100, 999)

        discussion = Discussion(id, student, topic, message, timestamp)

        self.discussions.append(discussion)
    
    def enroll_course(self, course):
        self.courses.append(course)
        course.enrolled_student.append(self.id)




