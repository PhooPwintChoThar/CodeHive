import persistent
from persistent import Persistent

class Quiz(persistent.Persistent):
    def __init__(self, id=0, title="", question="", languages="Any", sample_sol="", duedate=None, 
                 duration=0, restriction="None", total_s=0):
        self.id = id
        self.title = title
        self.languages=languages
        self.question = question
        self.sample_sol = sample_sol
        self.duedate = duedate
        self.duration = duration
        self.restriction = restriction
        self.total_s = total_s
        self.participated_students = {}
        self.professor_id = None  
        self.course_id = None  

    def show_student_list(self):
        return self.participated_students
    
    def show_student_result(self, id):
        return self.participated_students[id]

    

