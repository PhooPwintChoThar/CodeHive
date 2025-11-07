# ZODB Database Connection Guide

## Overview
This project uses **ZODB (Zope Object Database)**, a native object database for Python that allows you to store Python objects directly without ORM mapping.

## Database File Location
```
/Users/thirithaw/Downloads/CodeHive-main-2/DatabaseSetUp/mydata.fs
```

## Database Structure

### Collections (BTrees)
- `professors` - Stores Professor objects
- `courses` - Stores Course objects  
- `students` - Stores Student objects
- `quizzes` - Stores Quiz objects
- `discussions` - Stores Discussion objects
- `chat_histories` - Stores Chat history objects

### Models
All models inherit from `persistent.Persistent`:

1. **Professor** (`models/Professor.py`)
   - `id`: Professor ID
   - `name`: Professor name
   - `courses`: List of courses taught
   - Methods: `create_course()`, `create_quiz()`, `get_courses()`, `get_quizzes()`

2. **Student** (`models/Student.py`)
   - `id`: Student ID
   - `name`: Student name
   - `batch`: Student batch year
   - `courses`: List of enrolled courses
   - `paticipated_quizzes`: List of quizzes taken
   - `discussions`: List of discussions created
   - Methods: `enroll_course()`, `join_quiz()`, `create_discussion()`

3. **Course** (`models/Course.py`)
   - `id`: Course ID
   - `name`: Course name
   - `professor`: Professor ID
   - `file_path`: Path to course materials
   - `curriculum`: Curriculum year
   - `enrolled_student`: List of enrolled student IDs
   - `quizzes`: List of quizzes

4. **Quiz** (`models/Quiz.py`)
   - `id`: Quiz ID
   - `title`: Quiz title
   - `question`: Quiz question
   - `sample_sol`: Sample solution
   - `total_s`: Total score
   - `restriction`: Code restrictions
   - `participated_students`: List of students who took the quiz
   - `duedate`: Due date
   - `duration`: Duration in minutes

## Usage Methods

### Method 1: Using DatabaseManager Class (Recommended)

```python
from db_connection import DatabaseManager

# Using context manager (auto-closes connection)
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    # Access collections
    professors = root['professors']
    students = root['students']
    
    # Read data
    for prof_id, prof in professors.items():
        print(f"Professor: {prof.name}")
    
    # Add data
    from models.Student import Student
    new_student = Student(67011002, "Jane Doe", 67)
    root['students'][67011002] = new_student
    
    # Commit changes
    db.commit()
```

### Method 2: Using Helper Functions

```python
from db_connection import init_database, get_root, close_database
import transaction

# Initialize
root = init_database('mydata.fs')

# Access data
students = root['students']
student = students[67011000]
print(student.name)

# Modify data
student.name = "New Name"
transaction.commit()

# Close when done
close_database()
```

### Method 3: Direct ZODB Connection

```python
import ZODB
import ZODB.FileStorage
import transaction

# Connect
storage = ZODB.FileStorage.FileStorage('mydata.fs')
db = ZODB.DB(storage)
connection = db.open()
root = connection.root()

# Use database
professors = root['professors']

# Commit and close
transaction.commit()
connection.close()
db.close()
```

### Method 4: FastAPI Integration (Current Implementation)

```python
from fastapi import FastAPI
import ZODB, ZODB.FileStorage
import globals
import transaction

app = FastAPI()

@app.on_event("startup")
def startup_event():
    storage = ZODB.FileStorage.FileStorage('mydata.fs')
    db = ZODB.DB(storage)
    globals.db = db
    globals.connection = globals.db.open()
    globals.root = globals.connection.root()

@app.on_event("shutdown")
def shutdown_event():
    if globals.connection:
        globals.connection.close()
    globals.db.close()

# Use in routes
@app.get("/students")
def get_students():
    students = globals.root['students']
    return {"count": len(students)}
```

## Common Operations

### Reading Data

```python
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    # Get all students
    students = root['students']
    
    # Get specific student
    student = students[67011000]
    print(f"Name: {student.name}")
    print(f"Courses: {len(student.courses)}")
    
    # Iterate through collection
    for student_id, student in students.items():
        print(f"{student_id}: {student.name}")
```

### Adding Data

```python
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    from models.Student import Student
    
    # Create new student
    new_student = Student(67011003, "Alice Smith", 67)
    
    # Add to database
    root['students'][67011003] = new_student
    
    # Commit
    db.commit()
```

### Updating Data

```python
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    # Get student
    student = root['students'][67011000]
    
    # Modify
    student.name = "Updated Name"
    
    # Mark as modified (if needed)
    student._p_changed = True
    
    # Commit
    db.commit()
```

### Deleting Data

```python
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    # Delete student
    if 67011003 in root['students']:
        del root['students'][67011003]
        db.commit()
```

### Querying/Filtering

```python
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    students = root['students']
    
    # Filter by batch
    batch_67 = [s for s in students.values() if s.batch == 67]
    
    # Find students with courses
    enrolled = [s for s in students.values() if len(s.courses) > 0]
    
    # Search by name
    matching = [s for s in students.values() if "Thaw" in s.name]
```

## Transaction Management

```python
with DatabaseManager('mydata.fs') as db:
    root = db.root
    
    try:
        # Make changes
        student = Student(99999, "Test", 67)
        root['students'][99999] = student
        
        # Commit if successful
        db.commit()
        
    except Exception as e:
        # Rollback on error
        db.abort()
        print(f"Error: {e}")
```

## Database Statistics

```python
with DatabaseManager('mydata.fs') as db:
    # Get stats
    stats = db.get_stats()
    print(stats)
    # Output: {'professors': 1, 'students': 1, 'courses': 1, ...}
    
    # List collections
    collections = db.list_collections()
    print(collections)
```

## Best Practices

1. **Always commit transactions** after modifications
2. **Use context managers** to ensure proper cleanup
3. **Handle exceptions** and rollback on errors
4. **Mark objects as changed** if ZODB doesn't detect changes: `obj._p_changed = True`
5. **Close connections** when done to release file locks
6. **Use BTrees** for large collections (already implemented)
7. **Avoid circular references** between persistent objects

## Running Examples

```bash
cd /Users/thirithaw/Downloads/CodeHive-main-2/DatabaseSetUp
python db_usage_examples.py
```

## Troubleshooting

### Database locked
- Ensure no other process is using the database
- Check for `.fs.lock` file and remove if stale

### Changes not persisting
- Make sure to call `transaction.commit()` or `db.commit()`
- Mark objects as changed: `obj._p_changed = True`

### Import errors
- Ensure all model files are in the `models/` directory
- Check that `__init__.py` exists in models folder

## Dependencies

```bash
pip install ZODB
pip install BTrees
pip install persistent
```

## File Structure

```
DatabaseSetUp/
├── mydata.fs              # Main database file
├── mydata.fs.index        # Database index
├── mydata.fs.lock         # Lock file
├── mydata.fs.tmp          # Temporary file
├── db_connection.py       # Database connection manager
├── db_usage_examples.py   # Usage examples
├── globals.py             # Global variables
├── main.py                # FastAPI application
└── models/
    ├── Professor.py
    ├── Student.py
    ├── Course.py
    ├── Quiz.py
    ├── Discussion.py
    └── Chat_history.py
```

## Next Steps

Now that you have the database connection set up, you can:
1. Provide your project description
2. I'll help you generate Python backend code
3. We can create API endpoints, business logic, or data processing scripts

Ready for your project description! 🚀
