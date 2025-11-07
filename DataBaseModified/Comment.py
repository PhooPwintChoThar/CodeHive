import persistent
from datetime import datetime
import transaction


class Comment(persistent.Persistent):
    """Comment model for discussion posts"""
    
    def __init__(self, id, discussion_id, student_id, student_name, content, timestamp=None):
        self.id = id
        self.discussion_id = discussion_id
        self.student_id = student_id
        self.student_name = student_name
        self.content = content
        self.timestamp = timestamp if timestamp else datetime.now()
        self.liked_by = []  # List of student IDs who liked this comment
    
    def like(self, student_id):
        """Add a like from a student"""
        if student_id not in self.liked_by:
            self.liked_by.append(student_id)
            self._p_changed = True
            return True
        return False
    
    def unlike(self, student_id):
        """Remove a like from a student"""
        if student_id in self.liked_by:
            self.liked_by.remove(student_id)
            self._p_changed = True
            return True
        return False
    
    def toggle_like(self, student_id):
        """Toggle like for a student (like if not liked, unlike if already liked)"""
        if student_id in self.liked_by:
            self.unlike(student_id)
            transaction.commit()
            return False  # Unliked
        else:
            self.like(student_id)
            transaction.commit()
            return True  # Liked
    
    def get_like_count(self):
        """Get total number of likes"""
        return len(self.liked_by)
    
    def is_liked_by(self, student_id):
        """Check if a student has liked this comment"""
        return student_id in self.liked_by
    
    def to_dict(self):
        """Convert comment to dictionary for API response"""
        return {
            "id": self.id,
            "discussion_id": self.discussion_id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "like_count": self.get_like_count(),
            "liked_by": list(self.liked_by)
        }
