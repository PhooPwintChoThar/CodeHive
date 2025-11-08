import persistent
import persistent.mapping

class Discussion(persistent.Persistent):
    def __init__(self, id, student, topic, message, timestamp):
        self.id = id
        self.student = student
        self.topic = topic
        self.message = message
        self.comment = persistent.mapping.PersistentMapping()
        self.like_counts = 0
        self.timestamp = timestamp
    
    def create_comment(self, student, content):
        self.comment[student] = content
        self._p_changed = True 
    
    def like(self):
        self.like_counts += 1
        self._p_changed = True
    
    def dislike(self):
        if self.like_counts > 0:
            self.like_counts -= 1
        self._p_changed = True