from fastapi import FastAPI,Request,Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import time
from ai_assistant import CodeEvaluator, TeacherAssistant
#Database
import ZODB, ZODB.FileStorage
import BTrees._OOBTree
import transaction
from models import Professor, Student, Discussion,Chat_history,Quiz,Course
import globals 
from datetime import date,datetime
from data import Courses, Students,Professors
app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates=Jinja2Templates(directory="templates")
code_evaluator=CodeEvaluator()
teacher_assistant=TeacherAssistant()


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
    
    
    for c in Courses:
        if c[0] not in globals.root["courses"]:
            course=Course.Course(c[0],c[1],c[2],c[3])
            globals.root["courses"][c[0]]=course
            transaction.commit()
    
    for p in Professors:
        
        if p[0] not in globals.root["professors"]:
            prof=Professor.Professor(p[0], p[1])
            globals.root["professors"][p[0]]=prof
            transaction.commit()
        profe=globals.root["professors"][p[0]]
        for cr in p[2]:
            if cr not in profe.courses:
                cou=globals.root["courses"][cr]
                profe.courses.append(cou)
                cou.professor=profe.name
        transaction.commit()
        
    
    for s in Students:
        if s[0] not in globals.root["students"]:
            student=Student.Student(s[0], s[1], s[2])
            globals.root["students"][s[0]]=student
            transaction.commit()
        stu=globals.root["students"][s[0]]
        course_list=globals.root["courses"]
        for c in course_list:
            if course_list[c].curriculum==((datetime.now().year+543)%100-stu.batch+1)*10+1:
                stu.enroll_course(course_list[c])
        transaction.commit(
            
        )
            
                
                
    

    
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
@app.get("/student/{id}/quizzes", response_class=HTMLResponse)
async def show_quizzes(id: int, request: Request):
    student = globals.root["students"][id]
    quizzes = []
    
    for course in student.courses:
        for quiz in course.get_quizzes():
            if quiz not in student.paticipated_quizzes:
                quizzes.append(quiz)

    quizzes = list(set(quizzes))
    
    quizzes.sort(key=lambda x: x.duedate, reverse=True)
    
    return templates.TemplateResponse(
        "student_quizzes.html", 
        {
            "request": request, 
            "student_id": id,  
            "quizzes": quizzes, 
            "version": int(time.time())
        }
    )
   
@app.get("/student/{sid}/quiz/{id}/solve", response_class=HTMLResponse)
async def show_form(sid:int, id:int,request:Request):
    quiz=globals.root["quizzes"][id]
    return templates.TemplateResponse("student_quiz_answer.html", {"request":request, "quiz":quiz, "sid":sid, "version": int(time.time())})


@app.post("/student/{sid}/quiz/{id}/submit", response_class=HTMLResponse)
async def submit_quiz(request:Request, sid:int, id:int, student_code:str=Form(...)):
    quiz=globals.root["quizzes"][id]
    student=globals.root["students"][sid]
    quiz.participated_students.append(student)
    student.join_quiz(quiz)
    calculated_result=code_evaluator.evaluate_code(quiz.question,quiz.sample_sol,student_code,quiz.languages,quiz.restriction,quiz.total_s)
    print(calculated_result)
    quizzes=[]
    for c in student.courses:
            quizzes+=c.get_quizzes()
    return templates.TemplateResponse("student_quizzes.html", {"request":request, "student_id":sid,  "quizzes":quizzes, "version": int(time.time())})

@app.get("/student/{id}/discussions", response_class=HTMLResponse)
async def show_discussions(id:int, request:Request):
    discussions = list(globals.root["discussions"].values())
    discussions.sort(key=lambda x: x.timestamp, reverse=True)
    student = globals.root["students"][id]
    return templates.TemplateResponse("student_discussions.html", {
        "request":request, 
        "id":id, 
        "discussions": discussions,
        "student_name": student.name, 
        "version": int(time.time())
    })

@app.post("/student/{id}/discussion/new")
async def create_discussion(id:int, topic:str=Form(...), message:str=Form(...)):
    d_list=globals.root["discussions"]
    discussion_id = max(d_list.keys()) + 1 if d_list else 1
    timestamp = datetime.now()
    
    new_discussion = Discussion.Discussion(discussion_id, id, topic, message, timestamp)
    globals.root["discussions"][discussion_id] = new_discussion
    transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/edit")
async def edit_discussion(id:int, disc_id:int, topic:str=Form(...), message:str=Form(...)):
    discussion = globals.root["discussions"][disc_id]
    if discussion.student == id:
        discussion.topic = topic
        discussion.message = message
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/delete")
async def delete_discussion(id:int, disc_id:int):
    discussion = globals.root["discussions"][disc_id]
    if discussion.student == id:
        del globals.root["discussions"][disc_id]
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/comment")
async def add_comment(id:int, disc_id:int, content:str=Form(...)):
    discussion = globals.root["discussions"][disc_id]
    discussion.create_comment(id, content)
    transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/comment/delete")
async def delete_comment(id:int, disc_id:int, comment_student_id:int=Form(...)):
    discussion = globals.root["discussions"][disc_id]   
    if comment_student_id == id and id in discussion.comment:
        del discussion.comment[id]
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

@app.get("/student/{id}/courses", response_class=HTMLResponse)
async def show_courses(id:int, request:Request):
    student=globals.root["students"][id]
    courses=student.courses
    
    return templates.TemplateResponse("student_courses.html", {"request":request, "id":id, "courses":courses, "version": int(time.time())})

@app.get("/student/{id}/chat/{chatid}", response_class=HTMLResponse)
async def show_chat(id:int, chatid:int, request:Request):
    chatlist=globals.root["chat_histories"]
    course_id=int(str(chatid)[len(str(id)):])
    course=globals.root["courses"][course_id]
    if chatid not in chatlist:
        chatlist[chatid]=Chat_history.Chat_history(chatlist)
        chatlist[chatid].messages.append({"role": "TA",
                "content": "Hello! I'm your AI tutor. How can I help you with your studies today?"})
        transaction.commit()
    return templates.TemplateResponse("student_chat.html", {"request":request, "id":id, "course":course,"history":chatlist[chatid].messages,"chatid":chatid, "version": int(time.time())})

@app.post("/student/{student_id}/chat/{chat_id}", response_class=HTMLResponse)
def send_prompt(student_id:int, chat_id:int, question:str=Form(...)):
    history=globals.root["chat_histories"][chat_id].messages
    history.append({"role":"student", "content":question})
    course_id=int(str(chat_id)[len(str(student_id)):])
    course=globals.root["courses"][course_id]
    filepath=course.file_path
    print(filepath)
    response=teacher_assistant.chat(question, filepath)
    history.append({"role":"TA", "content":response})
    
    return RedirectResponse(f"/student/{student_id}/chat/{chat_id}", status_code=303)



@app.get("/professor/{id}/quizzes", response_class=HTMLResponse)
async def show_created_quizzes(request:Request, id:int):
    quizzes=globals.root["professors"][id].get_quizzes()
    return templates.TemplateResponse("teacher_quizzes.html", {"request":request,"id":id, "quizzes":quizzes, "version": int(time.time())})


@app.get("/professor/{id}/quiz/new", response_class=HTMLResponse)
async def show_create_quiz(id:int, request:Request):
    curr_prof=globals.root["professors"][id]
    courses=curr_prof.get_courses()
    
    return templates.TemplateResponse("teacher_create_quiz.html", {"request":request, "id":id, "courses":courses, "version": int(time.time())})


@app.post("/professor/{id}/quiz/new")
async def create_quiz(request:Request,id:int, title:str=Form(...), course: int=Form(...), question:str=Form(...), sample_output:str=Form(...), duedate:date=Form(...), duration:int=Form(...),restriction:str=Form("None"),languages:str=("Any") ,total_s:int=Form(...)):
    prof=globals.root["professors"][id]
    quiz_list = globals.root["quizzes"]
    quiz_id = max(quiz_list.keys()) + 1 if quiz_list else 1  
    quiz = Quiz.Quiz(quiz_id, title, question,languages, sample_output, duedate, duration, restriction, total_s)
    quiz.professor_id=id
    quiz.course_id=course
    globals.root["quizzes"][quiz_id] = quiz  
    print(globals.root["quizzes"][quiz_id].title + " is added")
    transaction.commit()
    courses=prof.get_courses()
    
    return templates.TemplateResponse(
        "teacher_create_quiz.html",
        {
            "request":request,
            "id":id,
            "courses":courses,
            "message": "Quiz created successfully!",
            "version": int(time.time())
        }
    )
    

@app.get("/professor/{id}/quiz/submissions", response_class=HTMLResponse)
async def show_quiz_submissions(id:int, request:Request):
    return templates.TemplateResponse("teacher_submissions.html", {"request":request, "id":id, "version": int(time.time())})


@app.get("/professor/{id}/quiz/responses", response_class=HTMLResponse)
async def show_quiz_submissions(id:int, request:Request):
    return templates.TemplateResponse("teacher_responses.html", {"request":request, "version": int(time.time())})
