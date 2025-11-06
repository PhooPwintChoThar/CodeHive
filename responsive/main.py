from fastapi import FastAPI,Request,Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import time
from ai_assistant import CodeEvaluator
import database
from models import testData

#Database
import ZODB, ZODB.FileStorage
import BTrees._OOBTree
import transaction
from models import Professor
import globals 

app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates=Jinja2Templates(directory="templates")
code_evaluator=CodeEvaluator()

@app.on_event("startup")
def startup_event():
    globals.connection = globals.db.open()
    globals.root = globals.connection.root()
    class_names = ['professors', 'courses', 'students', 'quizzes', 'discussions', 'chat_histories']
    for c in class_names:
        if c not in globals.root:
            globals.root[c] = BTrees._OOBTree.BTree()

    python_prof = Professor.Professor(111, "Dr.Visit Hirankitti")
    python_prof.create_course("Python", "/data/python")
    python_prof.create_quiz(
        """Find the first non-repeating character in a string.
        Return its index. If it doesn’t exist, return -1.
        Example:
        Input: "leetcode"
        Output: 0
        Explanation: 'l' is the first non-repeating character.""",
        """def firstUniqChar(s):
        freq = {}
        for ch in s:
            if ch in freq:
                freq[ch] += 1
            else:
                freq[ch] = 1
        
        for i in range(len(s)):
            if freq[s[i]] == 1:
                return i
        
        return -1  # if no unique character
        """, 5, "none"
    )

    globals.root["professors"][111] = python_prof
    transaction.commit()
    
@app.on_event("shutdown")
def shutdown_event():
    if globals.connection:
        globals.connection.close()
    globals.db.close()

@app.get("/", response_class=HTMLResponse)
async def show_home(request:Request):
    return templates.TemplateResponse("home_page.html", {"request":request, "version": int(time.time())})


@app.get("/student/courses", response_class=HTMLResponse)
async def show_courses(request:Request):
    return templates.TemplateResponse("student_courses.html", {"request":request})

@app.get("/student/chat", response_class=HTMLResponse)
async def show_chat(request:Request):
    return templates.TemplateResponse("student_chat.html", {"request":request})


@app.get("/student/discussions", response_class=HTMLResponse)
async def show_discussions(request:Request):
    return templates.TemplateResponse("student_discussions.html", {"request":request})

@app.get("/student/quizzes", response_class=HTMLResponse)
async def show_quizzes(request:Request):
    id=111
    quizzes=[]
    professor_list=globals.root["professors"]
    if professor_list:
        if id in professor_list:
            quizzes+=professor_list[id].get_quizzes()
    return templates.TemplateResponse("student_quizzes.html", {"request":request, "quizzes":quizzes})

@app.get("/student/quiz/solve", response_class=HTMLResponse)
async def show_form(request:Request):
    return templates.TemplateResponse("student_quiz_answer.html", {"request":request})

@app.post("/student/quiz/submit", response_class=HTMLResponse)
async def submit_quiz(student_code:str=Form(...)):
    #result="<!DOCTYPE html><html><head></head><body>"
    if(student_code):
        question="""Find the first non-repeating character in a string.
                    Return its index. If it doesn’t exist, return -1.
                    Example:
                    Input: "leetcode"
                    Output: 0
                    Explanation: 'l' is the first non-repeating character."""
        reference="""def firstUniqChar(s):
                    freq = {}
                    for ch in s:
                        if ch in freq:
                            freq[ch] += 1
                        else:
                            freq[ch] = 1
                    
                    for i in range(len(s)):
                        if freq[s[i]] == 1:
                            return i
                    
                    return -1  # if no unique character

                    """
        language="python"
        
        restricted="builtin-functions like count()"
        total_score=5
        
        calculated_result=code_evaluator.evaluate_code(question,reference,student_code,language,restricted,total_score)
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
    return templates.TemplateResponse("teacher_quizzes.html", {"request":request, "quizzes":quizzes})


@app.get("/teacher/quiz/new", response_class=HTMLResponse)
async def show_create_quiz(request:Request):
    return templates.TemplateResponse("teacher_create_quiz.html", {"request":request})


@app.post("/professor/quiz/new")
async def create_quiz():
    pass

@app.get("/teacher/quiz/submissions", response_class=HTMLResponse)
async def show_quiz_submissions(request:Request):
    return templates.TemplateResponse("teacher_submissions.html", {"request":request})


@app.get("/teacher/quiz/responses", response_class=HTMLResponse)
async def show_quiz_submissions(request:Request):
    return templates.TemplateResponse("teacher_responses.html", {"request":request})