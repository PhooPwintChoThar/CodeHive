from fastapi import FastAPI,Request,Form,Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict
import time

#AI tools
from ai_assistant import CodeEvaluator, TeacherAssistant,QuestionChecker


#Database
import ZODB, ZODB.FileStorage
import BTrees._OOBTree
import transaction
from models import Professor, Student, Discussion,Chat_history,Quiz,Course,Response
import globals 
from datetime import date,datetime
from data import Courses, Students,Professors, SKILLS


#ast
import ast
from difflib import SequenceMatcher

class ASTNormalizer(ast.NodeVisitor): 
    def __init__(self):
        self.structure = []
        self.var_counter = 0
        self.var_map = {}
        
    def generic_visit(self, node):
        self.structure.append(type(node).__name__)
        super().generic_visit(node)
        
    def visit_Name(self, node):
        if node.id not in self.var_map:
            self.var_map[node.id] = f"VAR_{self.var_counter}"
            self.var_counter += 1
        self.structure.append(f"Name:{self.var_map[node.id]}")
        
    def visit_Constant(self, node):
        self.structure.append(f"Const:{type(node.value).__name__}")


def normalize_code_ast(code: str) -> List[str]:
    try:
        tree = ast.parse(code)
        normalizer = ASTNormalizer()
        normalizer.visit(tree)
        return normalizer.structure
    except:
        return []

def tree_edit_distance(tree1: ast.AST, tree2: ast.AST) -> int:
    def get_node_signature(node):
        if isinstance(node, ast.Name):
            return "Name"
        elif isinstance(node, ast.Constant):
            return f"Const_{type(node.value).__name__}"
        else:
            return type(node).__name__
    
    def tree_to_list(node):
        result = [get_node_signature(node)]
        for child in ast.iter_child_nodes(node):
            result.extend(tree_to_list(child))
        return result
    
    list1 = tree_to_list(tree1)
    list2 = tree_to_list(tree2)
    
    m, n = len(list1), len(list2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if list1[i-1] == list2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    return dp[m][n]

def advanced_similarity(code1: str, code2: str) -> float:
    try:
        structure1 = normalize_code_ast(code1)
        structure2 = normalize_code_ast(code2)
        
        if not structure1 or not structure2:
            return 0.0
        
        matcher = SequenceMatcher(None, structure1, structure2)
        struct_similarity = matcher.ratio() * 100
        
        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)
        distance = tree_edit_distance(tree1, tree2)
        
        max_nodes = max(len(list(ast.walk(tree1))), len(list(ast.walk(tree2))))
        tree_similarity = max(0, (1 - distance / max_nodes) * 100) if max_nodes > 0 else 0
        
        return round((struct_similarity * 0.6 + tree_similarity * 0.4), 2)
    except:
        return 0.0


def compare_all_submissions(student_codes: Dict[int, str]) -> Dict:
    student_ids = list(student_codes.keys())
    pairwise = []
    stats = {sid: {"total": 0, "count": 0} for sid in student_ids}
    
    for i in range(len(student_ids)):
        for j in range(i + 1, len(student_ids)):
            id1, id2 = student_ids[i], student_ids[j]
            sim = advanced_similarity(student_codes[id1], student_codes[id2])

            pairwise.append({
                "student1_id": id1,
                "student2_id": id2,
                "similarity": sim,
                "flagged": sim > 75
            })

            stats[id1]["total"] += sim
            stats[id1]["count"] += 1
            stats[id2]["total"] += sim
            stats[id2]["count"] += 1

    individual = []
    for sid in student_ids:
        avg = (
            stats[sid]["total"] / stats[sid]["count"]
            if stats[sid]["count"] > 0 else 0
        )
        individual.append({
            "student_id": sid,
            "avg_similarity": round(avg, 2)
        })

    return {
        "pairwise": pairwise,
        "individual": individual,
        "flagged_count": sum(1 for x in pairwise if x["flagged"]),
        "total_comparisons": len(pairwise)
    }

def compare_across_quizzes(quiz_submissions: Dict[int, Dict[int, str]]) -> Dict:
    results = []
    
    quiz_ids = list(quiz_submissions.keys())
    
    for student_id in {sid for q in quiz_submissions.values() for sid in q}:
        for i in range(len(quiz_ids)):
            for j in range(i + 1, len(quiz_ids)):
                q1, q2 = quiz_ids[i], quiz_ids[j]
                
                if student_id in quiz_submissions[q1] and student_id in quiz_submissions[q2]:
                    sim = advanced_similarity(
                        quiz_submissions[q1][student_id],
                        quiz_submissions[q2][student_id]
                    )
                    
                    if sim > 50:
                        results.append({
                            "student_id": student_id,
                            "quiz1": q1,
                            "quiz2": q2,
                            "similarity": sim,
                            "flagged": sim > 75
                        })
    
    return {
        "cross_quiz_comparisons": results,
        "high_similarity_count": len(results)
    }

#FastAPI INITIALIZE
app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates=Jinja2Templates(directory="templates")
code_evaluator=CodeEvaluator()
teacher_assistant=TeacherAssistant()
question_checker=QuestionChecker()


@app.on_event("startup")
def startup_event():
    semester=2
    storage = ZODB.FileStorage.FileStorage('mydata.fs')
    db = ZODB.DB(storage)
    globals.db = db
    globals.connection = globals.db.open()
    globals.root = globals.connection.root()

    class_names = ['professors', 'courses', 'students', 'quizzes', 'discussions', 'chat_histories', 'responses']
    for c in class_names:
        if c not in globals.root:
            globals.root[c] = BTrees._OOBTree.BTree()
            transaction.commit()
    
    
    for c in Courses:
        if c[0] not in globals.root["courses"]:
            course=Course.Course(c[0],c[1],c[2])
            globals.root["courses"][c[0]]=course
            transaction.commit()
    
    for p in Professors:
        
        if p[0] not in globals.root["professors"]:
            prof=Professor.Professor(p[0], p[1])
            globals.root["professors"][p[0]]=prof
            transaction.commit()
        profe=globals.root["professors"][p[0]]
        for cr in p[2]:
            cous=globals.root["courses"][cr] 
            if cous not in profe.courses and cous.curriculum%10==semester:
                profe.courses.append(cous)
                profe._p_changed = True  
                cous.professor=profe.name
        transaction.commit()
        
    
    for s in Students:
        if s[0] not in globals.root["students"]:
            student=Student.Student(s[0], s[1], s[2])
            for skill in SKILLS:
                student.skills[skill]=0
                student._p_changed=True
            globals.root["students"][s[0]]=student
            transaction.commit()
        stu=globals.root["students"][s[0]]
        course_list=globals.root["courses"]
        for c in course_list:
            if course_list[c].curriculum==((datetime.now().year+543)%100-stu.batch+1)*10+semester:
                stu.enroll_course(course_list[c])
        transaction.commit(
            
        )
            
                
@app.on_event("shutdown")
def shutdown_event():
    transaction.commit()
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
    if user_id in globals.root["professors"]:
        return RedirectResponse(f"/professor/{user_id}/quizzes", status_code=303)
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
    
    # Get all available quizzes from student's courses
    for course in student.courses:
        for quiz in course.get_quizzes():
            quizzes.append({
                "id": quiz.id,
                "title": quiz.title,
                "duedate": str(quiz.duedate),
                "question": quiz.question,
                "sample_sol": quiz.sample_sol,
                "duration": quiz.duration,
                "languages": quiz.languages,
                "restriction": quiz.restriction,
                "total_s": quiz.total_s
            })
    
    overdue_quizzes = []
    for quiz in quizzes:
        duedate = datetime.fromisoformat(quiz["duedate"])

        now = datetime.now()

        is_overdue = now > duedate
        
        if is_overdue:
            overdue_quizzes.append(quiz)
    
    
    participated_quiz_ids = list(student.paticipated_quizzes)
    unparticipated=[]
    quiz_responses = {}
    for qu in quizzes:
        if qu["id"] in globals.root["quizzes"]:
            quiz = globals.root["quizzes"][qu["id"]]
            if qu["id"] in participated_quiz_ids:
                if id in quiz.participated_students:
                    rid = quiz.participated_students[id]
                    if rid in globals.root["responses"]:
                        response = globals.root["responses"][rid]
                        quiz_responses[qu["id"]] = {
                            "score": response.score,
                            "mistakes": response.mistakes,
                            "comments": response.comments
                        }
            else:
                not_found=True
                for qq in overdue_quizzes:
                    if qq['id']==qu["id"]:
                        not_found=False
                if not_found:
                    unparticipated.append(quiz)
                
    
    return templates.TemplateResponse(
        "student_quizzes.html",
        {
            "request": request,
            "student_id": id,
            "quizzes": quizzes,
            "participated_quizzes": quiz_responses,
            "overdue_quizzes": overdue_quizzes,
            "unparticipated":unparticipated,
            "version": int(time.time())
        }
    )
@app.get("/student/{sid}/quiz/{id}/solve", response_class=HTMLResponse)
async def show_form(sid:int, id:int,request:Request):
    quiz=globals.root["quizzes"][id]
    return templates.TemplateResponse("student_quiz_answer.html", {"request":request, "quiz":quiz, "sid":sid, "version": int(time.time())})


@app.post("/student/{sid}/quiz/{id}/submit", response_class=HTMLResponse)
async def submit_quiz( sid: int, id: int, student_code: str = Form(...), system_log:str=Form(None)):
    if not student_code:
        student_code=""
    quiz = globals.root["quizzes"][id]
    student = globals.root["students"][sid]
    
    calculated_result = code_evaluator.evaluate_code(
        quiz.question, quiz.sample_sol, student_code, 
        quiz.languages, quiz.restriction, quiz.total_s
    )
    mathematical=[1006710,1006717,1006718,1006716,1006730,96642170,96642022]
    programming=[1286121,1286120,1286131,1286222,1286228,1286232,1286391,1286233]
    computer=[1286111,1286213,1286112]
    networking=[1286241,1286223]
    if(calculated_result[0]>0):
        if quiz.course_id in mathematical:
            student.skills["Mathematical & Analytical Skills"]+=1
            student._p_changed=True
            
        if quiz.course_id in programming:
            student.skills["Programming & Software Development Skills"]+=1
            student._p_changed=True
        
        if quiz.course_id in computer:
            student.skills["Computer Systems & Hardware Skills"]+=1
            student._p_changed=True
        
        if quiz.course_id in networking:
            student.skills["Data & Networking Skills"]+=1
            student._p_changed=True
    
    print(student.skills)
    
    res_list = globals.root["responses"]
    res_id = max(res_list.keys()) + 1 if res_list else 1
    
    response = Response.Response(
        res_id, quiz, student_code, calculated_result[0], 
        calculated_result[1], calculated_result[2], datetime.now()
    )
    if system_log:
        response.system_log=system_log.split('@')
    quiz.participated_students[sid] = res_id
    quiz._p_changed = True  
    
    globals.root["responses"][res_id] = response
    transaction.commit()
    
    student.join_quiz(id)
    student._p_changed = True 
    transaction.commit()
    
    print(calculated_result)
    quizzes = []
    for c in student.courses:
        quizzes += c.get_quizzes()
    
    return RedirectResponse(f"/student/{sid}/quizzes", status_code=303)
    
@app.get("/student/{id}/discussions", response_class=HTMLResponse)
async def show_discussions(id:int, request:Request):
    discussions=[]
    student = globals.root["students"][id]
    for d in globals.root["discussions"]:
        if globals.root["discussions"][d].student.batch==student.batch:
            discussions.append(globals.root["discussions"][d])
    discussions.sort(key=lambda x: x.timestamp, reverse=True)
    
    return templates.TemplateResponse("student_discussions.html", {
        "request":request, 
        "id":id, 
        "discussions": discussions,
        "student_name": student.name, 
        "version": int(time.time())
    })

@app.post("/student/{id}/discussion/new")
async def create_discussion(id:int, topic:str=Form(...), message:str=Form(...)):
    student=globals.root["students"][id]
    d_list=globals.root["discussions"]
    discussion_id = max(d_list.keys()) + 1 if d_list else 1
    timestamp = datetime.now()
    
    new_discussion = Discussion.Discussion(discussion_id, student, topic, message, timestamp)
    globals.root["discussions"][discussion_id] = new_discussion
    transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/edit")
async def edit_discussion(id:int, disc_id:int, topic:str=Form(...), message:str=Form(...)):
    student=globals.root["students"][id]
    discussion = globals.root["discussions"][disc_id]
    if discussion.student == student:
        discussion.topic = topic
        discussion.message = message
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/delete")
async def delete_discussion(id:int, disc_id:int):
    student=globals.root["students"][id]
    discussion = globals.root["discussions"][disc_id]
    if discussion.student == student:
        del globals.root["discussions"][disc_id]
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/comment")
async def add_comment(id:int, disc_id:int, content:str=Form(...)):
    student=globals.root["students"][id]
    discussion = globals.root["discussions"][disc_id]
    discussion.create_comment(student, content)
    transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

@app.post("/student/{id}/discussion/{disc_id}/comment/delete")
async def delete_comment(id:int, disc_id:int, comment_student_id:int=Form(...)):
    student=globals.root["students"][id]
    discussion = globals.root["discussions"][disc_id]   
    if comment_student_id == id and student in discussion.comment:
        del discussion.comment[student]
        transaction.commit()
    
    return RedirectResponse(f"/student/{id}/discussions", status_code=303)

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
        new_chat=Chat_history.Chat_history(chatid)
        globals.root["chat_histories"][chatid]=new_chat
        new_chat.messages.append({"role": "TA",
                "content": "Hello! I'm your AI tutor. How can I help you with your studies today?"})
        print(chatid, new_chat.messages, "added")
        new_chat._p_changed=True
        transaction.commit()
        print("database",globals.root["chat_histories"][chatid].messages)
    return templates.TemplateResponse("student_chat.html", {"request":request, "id":id, "course":course,"history":chatlist[chatid].messages,"chatid":chatid, "version": int(time.time())})

@app.post("/student/{student_id}/chat/{chat_id}", response_class=HTMLResponse)
def send_prompt(student_id:int, chat_id:int, question:str=Form(...)):
    chat_history = globals.root["chat_histories"][chat_id]
    chat_history.messages.append({"role":"student", "content":question})
    chat_history._p_changed=True
    course_id=int(str(chat_id)[len(str(student_id)):])
    course=globals.root["courses"][course_id]
    response=teacher_assistant.chat(question,  course.name)
    chat_history.messages.append({"role":"TA", "content":response})
    chat_history._p_changed = True
    transaction.commit()
    print("database",globals.root["chat_histories"][chat_id].messages)

    return RedirectResponse(f"/student/{student_id}/chat/{chat_id}", status_code=303)

@app.get("/student/{id}/profile", response_class=HTMLResponse)
def show_profile(id:int, request:Request):
    student=globals.root["students"][id]
    return templates.TemplateResponse("student_profile.html",{"request":request, "student":student,"skills":student.skills, "id":id} )




@app.get("/professor/{id}/quizzes", response_class=HTMLResponse)
async def show_created_quizzes(request:Request, id:int):
    prof=globals.root["professors"][id]
    quizzes=globals.root["professors"][id].get_quizzes()
    return templates.TemplateResponse("teacher_quizzes.html", {"request":request,"id":id, "quizzes":quizzes,"prof_name":prof.name, "version": int(time.time())})


@app.get("/professor/{id}/quiz/new", response_class=HTMLResponse)
async def show_create_quiz(id:int, request:Request):
    curr_prof=globals.root["professors"][id]
    courses=curr_prof.get_courses()
    
    return templates.TemplateResponse("teacher_create_quiz.html", {"request":request, "id":id, "courses":courses, "prof_name":curr_prof.name,"version": int(time.time())})

@app.post("/professor/{id}/quiz/validate")
async def validate_question(id: int, request: Request):
    """Validate question without creating quiz"""
    try:
        data = await request.json()
        question = data.get('question')
        course_id = data.get('course_id')
        sample_output = data.get('sample_output')
        restriction = data.get('restriction', 'None')

        if course_id not in globals.root["courses"]:
            return {"correct": False, "message": "Course not found"}
        
        course = globals.root["courses"][course_id]
        course_name = course.name

        question_check_result = question_checker.check(
            question, 
            course_name, 
            sample_output, 
            restriction
        )

        return question_check_result

    except Exception as e:
        print(f"Error validating question: {e}")
        return {"correct": False, "message": f"Validation error: {str(e)}"}


@app.post("/professor/{id}/quiz/new")
async def create_quiz(
    request: Request,
    id: int,
    title: str = Form(...),
    course: int = Form(...),
    question: str = Form(...),
    sample_output: str = Form(...),
    duedate: date = Form(...),
    duration: int = Form(...),
    restriction: str = Form("None"),
    languages: str = Form("Any"),
    total_s: int = Form(...)
):
    try:
        prof = globals.root["professors"][id]
        course_obj = globals.root["courses"][course]
        courses = prof.get_courses()

        question_check_result = question_checker.check(
            question, 
            course_obj.name, 
            sample_output, 
            restriction
        )

        quiz_list = globals.root["quizzes"]
        quiz_id = max(quiz_list.keys()) + 1 if quiz_list else 1
        
        quiz = Quiz.Quiz(
            quiz_id, 
            title, 
            question, 
            languages, 
            sample_output, 
            duedate, 
            duration, 
            restriction, 
            total_s
        )
        quiz.professor_id = id
        quiz.course_id = course
        
        globals.root["quizzes"][quiz_id] = quiz
        quiz._p_changed = True
        transaction.commit()
        
        print(globals.root["quizzes"][quiz_id].title + " is added")

        success_message = "Quiz created successfully!"
        
        return templates.TemplateResponse(
            "teacher_create_quiz.html",
            {
                "request": request,
                "id": id,
                "courses": courses,
                "message": success_message,
                "prof_name":prof.name,
                "version": int(time.time())
            }
        )

    except Exception as e:
        print(f"Error creating quiz: {e}")
        prof = globals.root["professors"][id]
        courses = prof.get_courses()
        
        return templates.TemplateResponse(
            "teacher_create_quiz.html",
            {
                "request": request,
                "id": id,
                "courses": courses,
                "message": f"Error creating quiz: {str(e)}",
                "prof_name":prof.name,
                "version": int(time.time())
            }
        )

@app.get("/professor/{id}/quiz/{qid}/submissions", response_class=HTMLResponse)
async def show_quiz_submissions(id:int,qid:int, request:Request):
    prof = globals.root["professors"][id]
    quiz=globals.root["quizzes"][qid]
    s_and_result={}
    for s in quiz.participated_students:
        stu=globals.root["students"][s]
        res=globals.root["responses"][quiz.participated_students[s]]
        s_and_result[stu]=res
    return templates.TemplateResponse("teacher_submissions.html", {"request":request, "id":id, "quiz":quiz, "student_result_list":s_and_result,"prof_name":prof.name, "version": int(time.time())})


@app.get("/professor/{id}/quiz/{qid}/{sid}/responses", response_class=HTMLResponse)
async def show_quiz_submissions(id:int,qid:int, sid:int, request:Request):
    prof = globals.root["professors"][id]
    quiz=globals.root["quizzes"][qid]
    print(quiz.participated_students)
    rid=quiz.participated_students[sid]
    response=globals.root["responses"][rid]
    student=globals.root["students"][sid]
    return templates.TemplateResponse("teacher_responses.html", {"request":request,"response":response,"student":student,"id":id, "qid":qid,"prof_name":prof.name,"version": int(time.time())})


@app.get("/professor/{pid}/quiz/{qid}/analysis", response_class=HTMLResponse)
async def quiz_analysis(request: Request, pid: int, qid: int):
    root = globals.root

    quiz = root["quizzes"][qid]
    cur_course=root["courses"][quiz.course_id]
    submissions = quiz.participated_students
    print(submissions , "SUBMMMM")

    has_submissions=  True if submissions else False
    student_codes = {}
    student_names = {}
    respons=root["responses"]
    for student in submissions:
        student_codes[student] = respons[submissions[student]].answer
        student_names[student] = root["students"][student].name

    current_analysis = compare_all_submissions(student_codes)


    return templates.TemplateResponse("quiz_analysis.html", {
        "request": request,
        "professor_id": pid,
        "quiz_id": qid,
        "current_quiz": quiz,
        "student_names": student_names,
        "current_analysis": current_analysis,
        "has_submissions":has_submissions
    })


@app.post("/professor/{id}/quiz/{qid}/{sid}/update-score")
async def update_score(id: int, qid: int, sid: int, score:int=Form(...) ):
    
    quiz=globals.root["quizzes"][qid]
    if  score:    
        if sid  in quiz.participated_students:
            rid = quiz.participated_students[sid]
            response = globals.root["responses"][rid]
            response.score = score
            response._p_changed = True
            quiz._p_changed=True
            transaction.commit()
    return RedirectResponse(f"/professor/{id}/quiz/{qid}/{sid}/responses", status_code=303)

@app.get("/professor/{id}/courses", response_class=HTMLResponse)
async def show_courses(id:int,request:Request):
    prof=globals.root["professors"][id]
    courses=prof.courses
    return templates.TemplateResponse("teacher_courses.html", {"request":request, "id":id, "courses":courses,"prof_name":prof.name})

@app.get("/professor/{id}/courses/{cid}/students", response_class=HTMLResponse)
async def show_students(id:int,cid:int,request:Request):
    prof = globals.root["professors"][id]
    course=globals.root["courses"][cid]
    students_list=[]
    enrolled_list=course.enrolled_student
    for s in enrolled_list:
        students_list.append(globals.root["students"][s])
        
    return templates.TemplateResponse("teacher_course_student_list.html", {"request":request, "id":id, "course":course, "students":students_list, "prof_name":prof.name})