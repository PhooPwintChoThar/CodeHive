import persistent


class Response(persistent.Persistent):
    def __init__(self, id=0, quiz=None, answer="", score=0, mistakes=None, comments=None, time_stamp=""):
        self.id=id
        self.quiz=quiz#object
        self.answer=answer
        self.score=score
        self.mistakes=mistakes
        self.comments=comments
        self.submitted_time=time_stamp
        self.system_log=None
        
        

    


