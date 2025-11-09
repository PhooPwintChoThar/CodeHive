import persistent
import persistent.mapping

class Discussion(persistent.Persistent):
    def __init__(self, id, student, topic, message, timestamp):
        self.id = id
        self.student = student #obj
        self.topic = topic
        self.message = message
        self.comment = persistent.mapping.PersistentMapping()
        self.timestamp = timestamp
    
    def create_comment(self, student, content):#obj
        self.comment[student] = content
        self._p_changed = True 
    
  