"""
Helper functions for Discussion operations
Following the same pattern as Professor.create_quiz()
"""
import random
import transaction
import globals
from models.Discussion import Discussion
from datetime import datetime


def create_discussion(student_id, student_name, topic, message):
    """Create a new discussion post"""
    discussion_list = globals.root["discussions"]
    
    # Generate unique ID
    discussion_id = random.randint(100000, 999999)
    while discussion_id in discussion_list:
        discussion_id = random.randint(100000, 999999)
    
    # Create discussion
    discussion = Discussion(
        id=discussion_id,
        student_id=student_id,
        student_name=student_name,
        topic=topic,
        message=message,
        timestamp=datetime.now()
    )
    
    # Save to database
    discussion_list[discussion_id] = discussion
    transaction.commit()
    
    return discussion


def delete_discussion(discussion_id, student_id):
    """Delete a discussion (only by creator)"""
    discussion_list = globals.root["discussions"]
    comments_collection = globals.root.get('comments', {})
    
    if discussion_id not in discussion_list:
        return False, "Discussion not found"
    
    discussion = discussion_list[discussion_id]
    
    # Check permission
    if discussion.student_id != student_id:
        return False, "You can only delete your own discussions"
    
    # Delete all comments
    for comment_id in list(discussion.comment_ids):
        if comment_id in comments_collection:
            del comments_collection[comment_id]
    
    # Delete discussion
    del discussion_list[discussion_id]
    transaction.commit()
    
    return True, "Discussion deleted successfully"


def get_all_discussions(student_id=None):
    """Get all discussions sorted by most recent"""
    discussion_list = globals.root["discussions"]
    discussions = []
    
    for disc_id, disc in discussion_list.items():
        disc_data = disc.to_dict()
        
        # Add comments
        comments = disc.get_comments()
        disc_data["comments"] = [c.to_dict() for c in comments]
        
        # Add is_liked_by_me flag
        if student_id:
            disc_data["is_liked_by_me"] = disc.is_liked_by(student_id)
            # Add flag for comments too
            for comment_data in disc_data["comments"]:
                comment_id = comment_data["id"]
                comment = globals.root['comments'].get(comment_id)
                if comment:
                    comment_data["is_liked_by_me"] = comment.is_liked_by(student_id)
        
        discussions.append(disc_data)
    
    # Sort by timestamp (most recent first)
    discussions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return discussions


def get_discussion(discussion_id, student_id=None):
    """Get a single discussion with comments"""
    discussion_list = globals.root["discussions"]
    
    if discussion_id not in discussion_list:
        return None
    
    discussion = discussion_list[discussion_id]
    disc_data = discussion.to_dict()
    
    # Add comments
    comments = discussion.get_comments()
    disc_data["comments"] = [c.to_dict() for c in comments]
    
    # Add is_liked_by_me flag
    if student_id:
        disc_data["is_liked_by_me"] = discussion.is_liked_by(student_id)
        # Add flag for comments too
        for comment_data in disc_data["comments"]:
            comment_id = comment_data["id"]
            comment = globals.root['comments'].get(comment_id)
            if comment:
                comment_data["is_liked_by_me"] = comment.is_liked_by(student_id)
    
    return disc_data
