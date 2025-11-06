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
from models import Professor, Student
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

    # ✅ Only create initial professor if not already in DB
    if 111 not in globals.root["professors"]:
        python_prof = Professor.Professor(111, "Dr.Visit Hirankitti")
        python_prof.create_course("Computer Programming", "/data/python", 1)
        globals.root["professors"][111] = python_prof
        transaction.commit()
    
    if 67011000 not in globals.root['students']:
        student=Student.Student(67011000, "Thaw Thar ", 67)
        curriculumn=(datetime.now().year+543)%100-student.batch
        courses_list=globals.root['courses']
        if courses_list:
            for c in courses_list:
                if courses_list[c].curriculum==curriculumn:
                    student.enroll_course(courses_list[c])
        globals.root['students'][67011000]=student
        

    
@app.on_event("shutdown")
def shutdown_event():
    if globals.connection:
        globals.connection.close()
    globals.db.close()

@app.get("/", response_class=HTMLResponse)
async def show_home(request:Request):
    return templates.TemplateResponse("home_page.html", {"request":request, "version": int(time.time())})


@app.get("/student/{id}/courses", response_class=HTMLResponse)
async def show_courses(id:int, request:Request):
    student=globals.root["students"][id]
    courses=student.courses
    
    return templates.TemplateResponse("student_courses.html", {"request":request, "id":id, "courses":courses})

@app.get("/student/chat", response_class=HTMLResponse)
async def show_chat(request:Request):
    return templates.TemplateResponse("student_chat.html", {"request":request})


@app.get("/student/{id}/discussions", response_class=HTMLResponse)
async def show_discussions(id:int, request:Request):
    return templates.TemplateResponse("student_discussions.html", {"request":request, "id":id})

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
async def submit_quiz(sid:int, id:int, student_code:str=Form(...)):
    quiz=globals.root["quizzes"][id]
    student=globals.root["students"][sid]
    student.join_quiz(quiz)
    calculated_result=code_evaluator.evaluate_code(quiz.question,quiz.sample_sol,student_code,quiz.title,quiz.restriction,quiz.total_s)
    print(calculated_result)
    #     result+=f"<h1>Score : {calculated_result[0]}</h1>"
    #     if len(calculated_result)>=2:
    #         result+=f"<h3 style='color:red;'>Mistakes : {calculated_result[1] } </h3>"
    #     if len(calculated_result)>=3:
    #         result+=f"<p>Comment : {calculated_result[2]}</p>"
    # else:
    #     result+=f"<h1>Score : 0</h1><p style='color:red;'>You didn't provide the answer</p>"
    
    # result+="</body></html>"
    
    return RedirectResponse("/student/quizzes", status_code=303)



@app.get("/professor/{id}/quizzes", response_class=HTMLResponse)
async def show_created_quizzes(request:Request, id:int):
    if id not in globals.root["professors"]:
        print("id not exist")
        return RedirectResponse("/", status_code=303)
    quizzes=globals.root["professors"][id].get_quizzes()
    return templates.TemplateResponse("teacher_quizzes.html", {"request":request,"id":id, "quizzes":quizzes})


@app.get("/teacher/{id}/quiz/new", response_class=HTMLResponse)
async def show_create_quiz(id:int, request:Request):
    curr_prof=globals.root["professors"][id]
    courses=curr_prof.get_courses()
    
    return templates.TemplateResponse("teacher_create_quiz.html", {"request":request, "id":id, "courses":courses})


@app.post("/professor/{id}/quiz/new")
async def create_quiz(request:Request,id:int, title:str=Form(...), course: int=Form(...), question:str=Form(...), sample_output:str=Form("not provided"), duedate:date=Form(...), duration:int=Form(...),restriction:str=Form("None"), total_s:int=Form(...)):
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

@app.get("/teacher/quiz/submissions", response_class=HTMLResponse)
async def show_quiz_submissions(request:Request):
    return templates.TemplateResponse("teacher_submissions.html", {"request":request})


@app.get("/teacher/quiz/responses", response_class=HTMLResponse)
async def show_quiz_submissions(request:Request):
    return templates.TemplateResponse("teacher_responses.html", {"request":request})