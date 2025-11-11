import persistent
from persistent.list import PersistentList
import persistent.mapping

class Student(persistent.Persistent):
    def __init__(self, id=0, name="", batch=68):
        self.id = id
        self.name = name
        self.paticipated_quizzes = PersistentList() 
        self.discussions = PersistentList()  
        self.courses = PersistentList()  
        self.chats = PersistentList()  
        self.batch = batch
        self.skills=persistent.mapping.PersistentMapping()

    def join_quiz(self, quiz_id):
        if quiz_id not in self.paticipated_quizzes:
            self.paticipated_quizzes.append(quiz_id)
            self._p_changed = True  
    
    def enroll_course(self, course):
        if course not in self.courses:
            self.courses.append(course)
            course.enrolled_student.append(self.id)
            course._p_changed=True




