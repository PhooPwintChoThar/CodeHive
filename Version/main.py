from fastapi import FastAPI,Request,Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import time
from ai_assistant import CodeEvaluator
#Database
import ZODB, ZODB.FileStorage
import BTrees._OOBTree
import transaction
from models import Professor, Student, Discussion
import globals 
from datetime import date,datetime

app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates=Jinja2Templates(directory="templates")
code_evaluator=CodeEvaluator()

@app.on_event("startup")
def startup_event():
    
    storage = ZODB.FileStorage.FileStorage('mydata.fs')
    db = ZODB.DB(storage)
    globals.db = db
    globals.connection = globals.db.open()
    globals.root = globals.connection.root()

    class_names = ['professors', 'courses', 'students', 'quizzes', 'discussions', 'chat_histories']
    for c in class_names:
        if c not in globals.root:
            globals.root[c] = BTrees._OOBTree.BTree()

    # Create initial professors
    if 111 not in globals.root["professors"]:
        python_prof = Professor.Professor(111, "Dr.Visit Hirankitti")
        python_prof.create_course("Computer Programming", "/data/python", 1)
        globals.root["professors"][111] = python_prof
        transaction.commit()
    
    if 222 not in globals.root["professors"]:
        math_prof = Professor.Professor(222, "Dr.Sarah Mitchell")
        math_prof.create_course("Advanced Mathematics", "/data/math", 2)
        globals.root["professors"][222] = math_prof
        transaction.commit()
    
    # Create initial students
    if 67011000 not in globals.root['students']:
        student=Student.Student(67011000, "Thaw Thar", 67)
        curriculumn=(datetime.now().year+543)%100-student.batch
        courses_list=globals.root['courses']
        if courses_list:
            for c in courses_list:
                if courses_list[c].curriculum==curriculumn:
                    student.enroll_course(courses_list[c])
        globals.root['students'][67011000]=student
        transaction.commit()
    
    if 67011001 not in globals.root['students']:
        student=Student.Student(67011001, "Alice Johnson", 67)
        curriculumn=(datetime.now().year+543)%100-student.batch
        courses_list=globals.root['courses']
        if courses_list:
            for c in courses_list:
                if courses_list[c].curriculum==curriculumn:
                    student.enroll_course(courses_list[c])
        globals.root['students'][67011001]=student
        transaction.commit()
    
    if 67011002 not in globals.root['students']:
        student=Student.Student(67011002, "Bob Smith", 67)
        curriculumn=(datetime.now().year+543)%100-student.batch
        courses_list=globals.root['courses']
        if courses_list:
            for c in courses_list:
                if courses_list[c].curriculum==curriculumn:
                    student.enroll_course(courses_list[c])
        globals.root['students'][67011002]=student
        transaction.commit()

    
@app.on_event("shutdown")
def shutdown_event():
    if globals.connection:
        globals.connection.close()
    globals.db.close()

@app.get("/", response_class=HTMLResponse)
async def show_home(request:Request):
    return templates.TemplateResponse("home_page.html", {"request":request, "version": int(time.time())})

@app.get("/login", response_class=HTMLResponse)
async def show_home(request:Request):
    return templates.TemplateResponse("login_page.html", {"request":request, "version": int(time.time())})

@app.post("/login")
async def login(request:Request, user_id:int=Form(...)):
    # Check if professor
    if user_id in globals.root["professors"]:
        return RedirectResponse(f"/professor/{user_id}/quizzes", status_code=303)
    # Check if student
    elif user_id in globals.root["students"]:
        return RedirectResponse(f"/student/{user_id}/quizzes", status_code=303)
    else:
        return templates.TemplateResponse("login_page.html", {
            "request":request, 
            "error": "Invalid ID. Please try again.",
            "version": int(time.time())
        })

@app.get("/student/{id}/courses", response_class=HTMLResponse)
async def show_courses(id:int, request:Request):
    student=globals.root["students"][id]
    courses=student.courses
    
    return templates.TemplateResponse("student_courses.html", {"request":request, "id":id, "courses":courses})

@app.get("/student/{id}/chat/{course_id}", response_class=HTMLResponse)
async def show_chat(id:int, course_id:int, request:Request):
    return templates.TemplateResponse("student_chat.html", {"request":request, "id":id, "course_id":course_id})


@app.get("/student/{id}/discussions", response_class=HTMLResponse)
async def show_discussions(id:int, request:Request):
    discussions = list(globals.root["discussions"].values())
    discussions.sort(key=lambda x: x.timestamp, reverse=True)
    student = globals.root["students"][id]
    return templates.TemplateResponse("student_discussions.html", {
        "request":request, 
        "id":id, 
        "discussions": discussions,
        "student_name": student.name
    })

@app.post("/student/{id}/discussion/new")
async def create_discussion(id:int, topic:str=Form(...), message:str=Form(...)):
    student = globals.root["students"][id]
    discussion_id = len(globals.root["discussions"]) + 1
    timestamp = datetime.now()
    
    new_discussion = Discussion.Discussion(discussion_id, student, topic, message, timestamp)
    globals.root["discussions"][discussion_id] = new_discussion
    transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/edit")
async def edit_discussion(id:int, disc_id:int, topic:str=Form(...), message:str=Form(...)):
    discussion = globals.root["discussions"][disc_id]
    if discussion.student.id == id:
        discussion.topic = topic
        discussion.message = message
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/delete")
async def delete_discussion(id:int, disc_id:int):
    discussion = globals.root["discussions"][disc_id]
    if discussion.student.id == id:
        del globals.root["discussions"][disc_id]
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/comment")
async def add_comment(id:int, disc_id:int, content:str=Form(...)):
    discussion = globals.root["discussions"][disc_id]
    student = globals.root["students"][id]
    discussion.create_comment(student, content)
    transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/comment/delete")
async def delete_comment(id:int, disc_id:int, comment_student_id:int=Form(...)):
    discussion = globals.root["discussions"][disc_id]
    student = globals.root["students"][comment_student_id]
    
    # Only allow deletion if the comment was made by the current user
    if comment_student_id == id and student in discussion.comment:
        del discussion.comment[student]
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/like")
async def like_discussion(id:int, disc_id:int):
    discussion = globals.root["discussions"][disc_id]
    discussion.like()
    transaction.commit()
    return {"likes": discussion.like_counts}

@app.post("/student/{id}/discussion/{disc_id}/dislike")
async def dislike_discussion(id:int, disc_id:int):
    discussion = globals.root["discussions"][disc_id]
    discussion.dislike()
    transaction.commit()
    return {"likes": discussion.like_counts}

@app.get("/student/{id}/quizzes", response_class=HTMLResponse)
async def show_quizzes(id:int,request:Request):
    quizzes=[]
    student=globals.root["students"][id]
    if student:
        for c in student.courses:
            quizzes+=c.get_quizzes()
    return templates.TemplateResponse("student_quizzes.html", {"request":request, "student_id":id,  "quizzes":quizzes})

@app.get("/student/{sid}/quiz/{id}/solve", response_class=HTMLResponse)
async def show_form(sid:int, id:int,request:Request):
    quiz=globals.root["quizzes"][id]
    return templates.TemplateResponse("student_quiz_answer.html", {"request":request, "quiz":quiz, "sid":sid})

@app.post("/student/{sid}/quiz/{id}/submit", response_class=HTMLResponse)
async def submit_quiz(request:Request, sid:int, id:int, student_code:str=Form(...)):
    quiz=globals.root["quizzes"][id]
    student=globals.root["students"][sid]
    quiz.participated_students.append(student)
    student.join_quiz(quiz)
    calculated_result=code_evaluator.evaluate_code(quiz.question,quiz.sample_sol,student_code,quiz.title,quiz.restriction,quiz.total_s)
    quizzes=[]
    for c in student.courses:
            quizzes+=c.get_quizzes()
    return templates.TemplateResponse("student_quizzes.html", {"request":request, "student_id":sid,  "quizzes":quizzes})



@app.get("/professor/{id}/quizzes", response_class=HTMLResponse)
async def show_created_quizzes(request:Request, id:int):
    if id not in globals.root["professors"]:
        return RedirectResponse("/", status_code=303)
    quizzes=globals.root["professors"][id].get_quizzes()
    return templates.TemplateResponse("teacher_quizzes.html", {"request":request,"id":id, "quizzes":quizzes})


@app.get("/teacher/{id}/quiz/new", response_class=HTMLResponse)
async def show_create_quiz(id:int, request:Request):
    curr_prof=globals.root["professors"][id]
    courses=curr_prof.get_courses()
    
    return templates.TemplateResponse("teacher_create_quiz.html", {"request":request, "id":id, "courses":courses})


@app.post("/professor/{id}/quiz/new")
async def create_quiz(request:Request,id:int, title:str=Form(...), course: int=Form(...), question:str=Form(...), sample_output:str=Form(...), duedate:date=Form(...), duration:int=Form(...),restriction:str=Form("None"), total_s:int=Form(...)):
    prof=globals.root["professors"][id]
    courses=prof.get_courses()
    prof.create_quiz(course, title, question, sample_output, duedate, duration, restriction, total_s)
    return templates.TemplateResponse(
        "teacher_create_quiz.html",
        {   "request":request,
         "id":id,
         "courses":courses,
            "message": "Quiz created successfully!"
        }
    )

@app.get("/professor/{id}/quiz/submissions", response_class=HTMLResponse)
async def show_quiz_submissions(id:int, request:Request):
    return templates.TemplateResponse("teacher_submissions.html", {"request":request, "id":id})


@app.get("/professor/{id}/quiz/responses", response_class=HTMLResponse)
async def show_quiz_submissions(id:int, request:Request):
    return templates.TemplateResponse("teacher_responses.html", {"request":request})