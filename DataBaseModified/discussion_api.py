"""
Discussion API Routes - Simplified (Active Record Pattern)
Matches the pattern used in Quiz APIs
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import globals
from models.DiscussionHelper import create_discussion, delete_discussion, get_all_discussions, get_discussion


router = APIRouter()


# ============= Request Models =============

class CreateDiscussionRequest(BaseModel):
    student_id: int
    student_name: str
    topic: str
    message: str


class CreateCommentRequest(BaseModel):
    student_id: int
    student_name: str
    content: str


class LikeRequest(BaseModel):
    student_id: int


# ============= Discussion Endpoints =============

@router.post("/discussions", status_code=201)
async def create_discussion_endpoint(request: CreateDiscussionRequest):
    """Create a new discussion post"""
    try:
        discussion = create_discussion(
            request.student_id,
            request.student_name,
            request.topic,
            request.message
        )
        
        return {
            "success": True,
            "message": "Discussion created successfully",
            "data": discussion.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating discussion: {str(e)}")


@router.get("/discussions")
async def get_all_discussions_endpoint(student_id: Optional[int] = None):
    """Get all discussions, sorted by most recent first"""
    try:
        discussions = get_all_discussions(student_id)
        
        return {
            "success": True,
            "count": len(discussions),
            "data": discussions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching discussions: {str(e)}")


@router.get("/discussions/{discussion_id}")
async def get_discussion_endpoint(discussion_id: int, student_id: Optional[int] = None):
    """Get a specific discussion by ID"""
    try:
        discussion = get_discussion(discussion_id, student_id)
        
        if not discussion:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        return {
            "success": True,
            "data": discussion
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching discussion: {str(e)}")


@router.delete("/discussions/{discussion_id}")
async def delete_discussion_endpoint(discussion_id: int, student_id: int):
    """Delete a discussion (only by the creator)"""
    try:
        success, message = delete_discussion(discussion_id, student_id)
        
        if not success:
            if "not found" in message:
                raise HTTPException(status_code=404, detail=message)
            else:
                raise HTTPException(status_code=403, detail=message)
        
        return {
            "success": True,
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting discussion: {str(e)}")


@router.post("/discussions/{discussion_id}/like")
async def like_discussion_endpoint(discussion_id: int, request: LikeRequest):
    """Like a discussion post"""
    try:
        discussions = globals.root['discussions']
        
        if discussion_id not in discussions:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        discussion = discussions[discussion_id]
        
        # Try to like
        success = discussion.like(request.student_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="You have already liked this discussion")
        
        # Commit is handled in the model method
        import transaction
        transaction.commit()
        
        return {
            "success": True,
            "message": "Discussion liked successfully",
            "like_count": discussion.get_like_count()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error liking discussion: {str(e)}")


@router.post("/discussions/{discussion_id}/unlike")
async def unlike_discussion_endpoint(discussion_id: int, request: LikeRequest):
    """Unlike a discussion post"""
    try:
        discussions = globals.root['discussions']
        
        if discussion_id not in discussions:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        discussion = discussions[discussion_id]
        
        # Try to unlike
        success = discussion.unlike(request.student_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="You haven't liked this discussion")
        
        # Commit
        import transaction
        transaction.commit()
        
        return {
            "success": True,
            "message": "Discussion unliked successfully",
            "like_count": discussion.get_like_count()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unliking discussion: {str(e)}")


# ============= Comment Endpoints =============

@router.post("/discussions/{discussion_id}/comments", status_code=201)
async def create_comment_endpoint(discussion_id: int, request: CreateCommentRequest):
    """Create a new comment on a discussion"""
    try:
        discussions = globals.root['discussions']
        
        if discussion_id not in discussions:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        discussion = discussions[discussion_id]
        
        # Create comment using model method
        comment = discussion.create_comment(
            request.student_id,
            request.student_name,
            request.content
        )
        
        return {
            "success": True,
            "message": "Comment created successfully",
            "data": comment.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating comment: {str(e)}")


@router.get("/discussions/{discussion_id}/comments")
async def get_comments_endpoint(discussion_id: int, student_id: Optional[int] = None):
    """Get all comments for a discussion"""
    try:
        discussions = globals.root['discussions']
        
        if discussion_id not in discussions:
            raise HTTPException(status_code=404, detail="Discussion not found")
        
        discussion = discussions[discussion_id]
        
        # Get comments using model method
        comments = discussion.get_comments()
        comments_data = []
        
        for comment in comments:
            comment_dict = comment.to_dict()
            
            # Add is_liked_by_me flag
            if student_id:
                comment_dict['is_liked_by_me'] = comment.is_liked_by(student_id)
            
            comments_data.append(comment_dict)
        
        return {
            "success": True,
            "count": len(comments_data),
            "data": comments_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {str(e)}")


@router.delete("/comments/{comment_id}")
async def delete_comment_endpoint(comment_id: int, student_id: int):
    """Delete a comment (only by the creator)"""
    try:
        comments_collection = globals.root.get('comments', {})
        
        if comment_id not in comments_collection:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        comment = comments_collection[comment_id]
        
        # Check permission
        if comment.student_id != student_id:
            raise HTTPException(status_code=403, detail="You can only delete your own comments")
        
        # Get the discussion and delete comment using model method
        discussion_id = comment.discussion_id
        discussions = globals.root['discussions']
        
        if discussion_id in discussions:
            discussion = discussions[discussion_id]
            discussion.delete_comment(comment_id)
        
        return {
            "success": True,
            "message": "Comment deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting comment: {str(e)}")


@router.post("/comments/{comment_id}/like")
async def like_comment_endpoint(comment_id: int, request: LikeRequest):
    """Like a comment"""
    try:
        comments_collection = globals.root.get('comments', {})
        
        if comment_id not in comments_collection:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        comment = comments_collection[comment_id]
        
        # Try to like
        success = comment.like(request.student_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="You have already liked this comment")
        
        # Commit
        import transaction
        transaction.commit()
        
        return {
            "success": True,
            "message": "Comment liked successfully",
            "like_count": comment.get_like_count()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error liking comment: {str(e)}")


@router.post("/comments/{comment_id}/unlike")
async def unlike_comment_endpoint(comment_id: int, request: LikeRequest):
    """Unlike a comment"""
    try:
        comments_collection = globals.root.get('comments', {})
        
        if comment_id not in comments_collection:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        comment = comments_collection[comment_id]
        
        # Try to unlike
        success = comment.unlike(request.student_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="You haven't liked this comment")
        
        # Commit
        import transaction
        transaction.commit()
        
        return {
            "success": True,
            "message": "Comment unliked successfully",
            "like_count": comment.get_like_count()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unliking comment: {str(e)}")
