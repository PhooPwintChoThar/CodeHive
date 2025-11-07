# Discussion API Documentation

Complete API documentation for the Discussion system with CRUD operations, likes, and comments.

## Base URL
```
http://localhost:8000/api
```

## Features
✅ Create, View, Delete discussions  
✅ Like/Unlike discussions (no duplicate likes)  
✅ Create, View, Delete comments  
✅ Like/Unlike comments (no duplicate likes)  
✅ Real-time updates  
✅ Permission checks (only creators can delete)  
✅ Sorted by most recent first  

---

## 📝 Discussion Endpoints

### 1. Create Discussion
**POST** `/discussions`

Create a new discussion post.

**Request Body:**
```json
{
  "student_id": 67011000,
  "student_name": "Thaw Thar",
  "topic": "Need help with Python loops",
  "message": "Can someone explain how while loops work?"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Discussion created successfully",
  "data": {
    "id": 123456,
    "student_id": 67011000,
    "student_name": "Thaw Thar",
    "topic": "Need help with Python loops",
    "message": "Can someone explain how while loops work?",
    "timestamp": "2025-11-07T20:00:00",
    "like_count": 0,
    "comment_count": 0,
    "liked_by": []
  }
}
```

---

### 2. Get All Discussions
**GET** `/discussions?student_id={student_id}`

Get all discussions sorted by most recent first.

**Query Parameters:**
- `student_id` (optional): Include to get `is_liked_by_me` flag

**Response (200):**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "id": 123456,
      "student_id": 67011000,
      "student_name": "Thaw Thar",
      "topic": "Need help with Python loops",
      "message": "Can someone explain how while loops work?",
      "timestamp": "2025-11-07T20:00:00",
      "like_count": 5,
      "comment_count": 3,
      "liked_by": [67011001, 67011002],
      "is_liked_by_me": false,
      "comments": [
        {
          "id": 789012,
          "discussion_id": 123456,
          "student_id": 67011001,
          "student_name": "John Doe",
          "content": "While loops continue until condition is false",
          "timestamp": "2025-11-07T20:05:00",
          "like_count": 2,
          "liked_by": [67011000]
        }
      ]
    }
  ]
}
```

---

### 3. Get Single Discussion
**GET** `/discussions/{discussion_id}?student_id={student_id}`

Get a specific discussion with all comments.

**Path Parameters:**
- `discussion_id`: Discussion ID

**Query Parameters:**
- `student_id` (optional): Include to get `is_liked_by_me` flag

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 123456,
    "student_id": 67011000,
    "student_name": "Thaw Thar",
    "topic": "Need help with Python loops",
    "message": "Can someone explain how while loops work?",
    "timestamp": "2025-11-07T20:00:00",
    "like_count": 5,
    "comment_count": 3,
    "liked_by": [67011001, 67011002],
    "is_liked_by_me": true,
    "comments": [...]
  }
}
```

**Error (404):**
```json
{
  "detail": "Discussion not found"
}
```

---

### 4. Delete Discussion
**DELETE** `/discussions/{discussion_id}?student_id={student_id}`

Delete a discussion (only by creator). Also deletes all associated comments.

**Path Parameters:**
- `discussion_id`: Discussion ID

**Query Parameters:**
- `student_id`: ID of student attempting to delete

**Response (200):**
```json
{
  "success": true,
  "message": "Discussion deleted successfully"
}
```

**Error (403):**
```json
{
  "detail": "You can only delete your own discussions"
}
```

---

### 5. Like Discussion
**POST** `/discussions/{discussion_id}/like`

Like a discussion post. Prevents duplicate likes.

**Path Parameters:**
- `discussion_id`: Discussion ID

**Request Body:**
```json
{
  "student_id": 67011000
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Discussion liked successfully",
  "like_count": 6
}
```

**Error (400):**
```json
{
  "detail": "You have already liked this discussion"
}
```

---

### 6. Unlike Discussion
**POST** `/discussions/{discussion_id}/unlike`

Remove like from a discussion post.

**Path Parameters:**
- `discussion_id`: Discussion ID

**Request Body:**
```json
{
  "student_id": 67011000
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Discussion unliked successfully",
  "like_count": 5
}
```

**Error (400):**
```json
{
  "detail": "You haven't liked this discussion"
}
```

---

## 💬 Comment Endpoints

### 7. Create Comment
**POST** `/discussions/{discussion_id}/comments`

Add a comment to a discussion.

**Path Parameters:**
- `discussion_id`: Discussion ID

**Request Body:**
```json
{
  "student_id": 67011001,
  "student_name": "John Doe",
  "content": "While loops continue until the condition is false"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Comment created successfully",
  "data": {
    "id": 789012,
    "discussion_id": 123456,
    "student_id": 67011001,
    "student_name": "John Doe",
    "content": "While loops continue until the condition is false",
    "timestamp": "2025-11-07T20:05:00",
    "like_count": 0,
    "liked_by": []
  }
}
```

---

### 8. Get Comments
**GET** `/discussions/{discussion_id}/comments?student_id={student_id}`

Get all comments for a discussion.

**Path Parameters:**
- `discussion_id`: Discussion ID

**Query Parameters:**
- `student_id` (optional): Include to get `is_liked_by_me` flag

**Response (200):**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "id": 789012,
      "discussion_id": 123456,
      "student_id": 67011001,
      "student_name": "John Doe",
      "content": "While loops continue until the condition is false",
      "timestamp": "2025-11-07T20:05:00",
      "like_count": 2,
      "liked_by": [67011000],
      "is_liked_by_me": true
    }
  ]
}
```

---

### 9. Delete Comment
**DELETE** `/comments/{comment_id}?student_id={student_id}`

Delete a comment (only by creator).

**Path Parameters:**
- `comment_id`: Comment ID

**Query Parameters:**
- `student_id`: ID of student attempting to delete

**Response (200):**
```json
{
  "success": true,
  "message": "Comment deleted successfully"
}
```

**Error (403):**
```json
{
  "detail": "You can only delete your own comments"
}
```

---

### 10. Like Comment
**POST** `/comments/{comment_id}/like`

Like a comment. Prevents duplicate likes.

**Path Parameters:**
- `comment_id`: Comment ID

**Request Body:**
```json
{
  "student_id": 67011000
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Comment liked successfully",
  "like_count": 3
}
```

**Error (400):**
```json
{
  "detail": "You have already liked this comment"
}
```

---

### 11. Unlike Comment
**POST** `/comments/{comment_id}/unlike`

Remove like from a comment.

**Path Parameters:**
- `comment_id`: Comment ID

**Request Body:**
```json
{
  "student_id": 67011000
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Comment unliked successfully",
  "like_count": 2
}
```

**Error (400):**
```json
{
  "detail": "You haven't liked this comment"
}
```

---

## 🔧 Testing the API

### Using cURL

**Create Discussion:**
```bash
curl -X POST http://localhost:8000/api/discussions \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 67011000,
    "student_name": "Thaw Thar",
    "topic": "Python Help",
    "message": "Need help with loops"
  }'
```

**Get All Discussions:**
```bash
curl http://localhost:8000/api/discussions?student_id=67011000
```

**Like Discussion:**
```bash
curl -X POST http://localhost:8000/api/discussions/123456/like \
  -H "Content-Type: application/json" \
  -d '{"student_id": 67011000}'
```

**Create Comment:**
```bash
curl -X POST http://localhost:8000/api/discussions/123456/comments \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 67011001,
    "student_name": "John Doe",
    "content": "Here is the answer..."
  }'
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Create discussion
response = requests.post(f"{BASE_URL}/discussions", json={
    "student_id": 67011000,
    "student_name": "Thaw Thar",
    "topic": "Python Help",
    "message": "Need help with loops"
})
print(response.json())

# Get all discussions
response = requests.get(f"{BASE_URL}/discussions?student_id=67011000")
print(response.json())

# Like discussion
response = requests.post(f"{BASE_URL}/discussions/123456/like", json={
    "student_id": 67011000
})
print(response.json())
```

---

## 🎯 Frontend Integration

The frontend is already connected in `student_discussions_new.html`:

- ✅ Auto-loads discussions on page load
- ✅ Create new discussions via modal
- ✅ Like/unlike with visual feedback
- ✅ Add comments (replies)
- ✅ Delete own posts/comments
- ✅ Real-time like counts
- ✅ Prevents duplicate likes
- ✅ Shows relative timestamps

---

## 🚀 Running the Application

1. **Start the server:**
```bash
cd /Users/thirithaw/Downloads/CodeHive-main-2/DatabaseSetUp
uvicorn main:app --reload
```

2. **Access the application:**
- Main app: http://localhost:8000
- Discussions: http://localhost:8000/student/67011000/discussions
- API docs: http://localhost:8000/docs

3. **View API documentation:**
FastAPI auto-generates interactive docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📊 Database Structure

### Collections:
- `discussions` - BTree of Discussion objects
- `comments` - BTree of Comment objects

### Discussion Model:
```python
{
    "id": int,
    "student_id": int,
    "student_name": str,
    "topic": str,
    "message": str,
    "timestamp": datetime,
    "comment_ids": [int],
    "liked_by": [int]
}
```

### Comment Model:
```python
{
    "id": int,
    "discussion_id": int,
    "student_id": int,
    "student_name": str,
    "content": str,
    "timestamp": datetime,
    "liked_by": [int]
}
```

---

## ✅ Features Implemented

- ✅ **Create** discussions and comments
- ✅ **View** all discussions with comments
- ✅ **Delete** own discussions and comments
- ✅ **Like/Unlike** discussions (no duplicates)
- ✅ **Like/Unlike** comments (no duplicates)
- ✅ **Permission checks** (only creators can delete)
- ✅ **Sorted by most recent** first
- ✅ **Visible to all students**
- ✅ **Real-time updates** in frontend
- ✅ **Responsive UI** with visual feedback

---

## 🐛 Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (duplicate like, etc.)
- `403` - Forbidden (permission denied)
- `404` - Not Found
- `500` - Internal Server Error

All errors include descriptive messages in the response.
