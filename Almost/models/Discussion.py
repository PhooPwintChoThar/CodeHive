import persistent
class Discussion(persistent.Persistent):
    def __init__(self, id, student, topic, message, timestamp):
        self.id = id
        self.student = student
        self.topic = topic
        self.message = message
        self.comment = {}
        self.like_counts = 0
        self.timestamp = timestamp
    
    def create_comment(self, student, content):
        self.comment[student] = content
    
    def like(self):
        self.like_counts += 1
    
    def dislike(self):
        self.like_counts -= 1