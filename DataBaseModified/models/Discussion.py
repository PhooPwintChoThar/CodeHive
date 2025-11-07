import persistent
from datetime import datetime
import random
import transaction
import globals
from models.Comment import Comment


class Discussion(persistent.Persistent):
    """Discussion post model with likes and comments"""
    
    def __init__(self, id, student_id, student_name, topic, message, timestamp=None):
        self.id = id
        self.student_id = student_id  # ID of student who created the post
        self.student_name = student_name  # Name of student who created the post
        self.topic = topic
        self.message = message
        self.timestamp = timestamp if timestamp else datetime.now()
        self.comment_ids = []  # List of comment IDs
        self.liked_by = []  # List of student IDs who liked this discussion
    
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
    
    def get_like_count(self):
        """Get total number of likes"""
        return len(self.liked_by)
    
    def is_liked_by(self, student_id):
        """Check if a student has liked this discussion"""
        return student_id in self.liked_by
    
    def add_comment(self, comment_id):
        """Add a comment ID to this discussion"""
        if comment_id not in self.comment_ids:
            self.comment_ids.append(comment_id)
            self._p_changed = True
    
    def remove_comment(self, comment_id):
        """Remove a comment ID from this discussion"""
        if comment_id in self.comment_ids:
            self.comment_ids.remove(comment_id)
            self._p_changed = True
    
    def get_comment_count(self):
        """Get total number of comments"""
        return len(self.comment_ids)
    
    def create_comment(self, student_id, student_name, content):
        """Create a new comment on this discussion"""
        comments_collection = globals.root['comments']
        
        # Generate unique ID
        comment_id = random.randint(100000, 999999)
        while comment_id in comments_collection:
            comment_id = random.randint(100000, 999999)
        
        # Create comment
        comment = Comment(
            id=comment_id,
            discussion_id=self.id,
            student_id=student_id,
            student_name=student_name,
            content=content,
            timestamp=datetime.now()
        )
        
        # Save comment
        comments_collection[comment_id] = comment
        self.add_comment(comment_id)
        transaction.commit()
        
        return comment
    
    def delete_comment(self, comment_id):
        """Delete a comment from this discussion"""
        comments_collection = globals.root['comments']
        
        if comment_id in comments_collection:
            del comments_collection[comment_id]
            self.remove_comment(comment_id)
            transaction.commit()
            return True
        return False
    
    def get_comments(self):
        """Get all comments for this discussion"""
        comments_collection = globals.root.get('comments', {})
        comments = []
        
        for comment_id in self.comment_ids:
            if comment_id in comments_collection:
                comments.append(comments_collection[comment_id])
        
        # Sort by timestamp (most recent first)
        comments.sort(key=lambda x: x.timestamp, reverse=True)
        return comments
    
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
    
    def to_dict(self, include_comments=False, comments_data=None):
        """Convert discussion to dictionary for API response"""
        result = {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "topic": self.topic,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "like_count": self.get_like_count(),
            "comment_count": self.get_comment_count(),
            "liked_by": list(self.liked_by)
        }
        
        if include_comments and comments_data:
            result["comments"] = comments_data
        
        return result