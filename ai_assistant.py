from openai import OpenAI
import os
import re

def getAPI():
    return OpenAI(
            api_key="your-openai-api-key", 
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:3000",  
                "X-Title": "Code Evaluator", 
            }
        )

class CodeEvaluator:
    def __init__(self):
        self.client=getAPI()
    
    def create_prompt(self, question:str, reference_code:str,student_code:str,  language:str, restricted_things:str, total_score:int):
    
        return f"""You are an expert {language} programming instructor evaluating student code submissions.

                    You are given:
                    - Question: {question}
                    - Reference Solution: {reference_code}
                    - Student Submission: {student_code}
                    - Restricted Technologies: {restricted_things} (if None, no restrictions apply)
                    - Total Score: {total_score}

                    Your evaluation rules:

                    1. A solution is acceptable even if it uses a completely different approach from the reference, as long as it produces correct results and satisfies the requirements.
                    2. Focus strictly on:
                    - correctness
                    - logic
                    - requirement satisfaction
                    - compliance with restrictions
                    3. If the student uses any restricted technology, the score must be 0.
                    4. If the solution does **not** fulfill the main problem requirement, score must be 0.
                    5. If the score is less than full marks, list every mistake clearly.
                    6. Comments are only for situations where the solution is technically correct but contains informal or questionable practices.
                    7. Your response must be **ONLY** in the following format — nothing else:

                    (score, mistakes, comments)

                    Where:
                    - score → integer from 0 to {total_score}
                    - mistakes → "None" if no mistakes, otherwise a single string describing mistakes
                    - comments → "None" if no comments, otherwise a single string describing comments

                    Do NOT include any extra wording or explanation outside this format.

                    """
                    
    def evaluate_code(self, question:str, reference_code:str,student_code:str,  language:str, restricted_things:str=None, total_score:int=10):
            if not all([question , reference_code, student_code]):
                return [0,None,"No answer submitted"]
            
            
            try:
                evaluation_prompt=self.create_prompt(question, reference_code,student_code,language,restricted_things,total_score)
                response = self.client.chat.completions.create(
                model="google/gemini-2.5-flash-lite", 
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert programming instructor who provides constructive, detailed feedback on code submissions. You evaluate code fairly, recognizing that multiple correct solutions exist for most problems."
                    },
                    {
                        "role": "user",
                        "content": evaluation_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )
                
                response_data=response.choices[0].message.content
                pattern = r"\(\s*(\d+)\s*,\s*(None|\".*?\"|'.*?'|[^,]+)\s*,\s*(None|\".*?\"|'.*?'|[^)]+)\s*\)"
                match = re.match(pattern, response_data.strip())
                if not match:
                    raise ValueError("AI response not in expected format (score, mistakes, comments)")

                score = int(match.group(1))
                mistakes = match.group(2).strip()
                comments = match.group(3).strip()
                
                return [score, mistakes, comments]
            except Exception as e:
                return [0,None,"Something wrong with AI response"]
        

class TeacherAssistant:
    def __init__(self):
        self.client = getAPI()
       

    def _detect_question_type(self, question):
        """Detect the type of question asked by student"""
        question_lower = question.lower()
        exercise_keywords = ["exercise", "practice", "challenge", "task", "problem"]
        resources_keywords = ["resource", "resources", "link", "website", "video", "reference"]
        notes_keywords = ["note", "notes", "main points", "summary", "outline"]
        explanation_keywords = ["explain", "what is", "meaning", "how does", "define"]

        if any(k in question_lower for k in exercise_keywords):
            return "exercise"
        elif any(k in question_lower for k in resources_keywords):
            return "resources"
        elif any(k in question_lower for k in notes_keywords):
            return "notes"
        elif any(k in question_lower for k in explanation_keywords):
            return "explanation"
        else:
            return "explanation"

    def _calculate_dynamic_max_tokens(self, question, question_type):
        question_length = len(question.split())
        base_tokens = 300
        
        if question_type == "exercise":
            base_tokens = 500
        elif question_type == "resources":
            base_tokens = 300
        elif question_type == "notes":
            base_tokens = 600
        elif question_type == "explanation":
            base_tokens = 400
        
        if question_length > 50:
            base_tokens += 150
        elif question_length > 30:
            base_tokens += 75
        
        return min(base_tokens, 1200)

    def chat(self, student_question: str, course_name: str) -> str:
       
        if not student_question or not student_question.strip():
            return "AI receives no question"
            
        
        if not course_name or not course_name.strip():
            return "AI receives no question"
        
        try:
            question_type = self._detect_question_type(student_question)
            max_tokens = self._calculate_dynamic_max_tokens(student_question, question_type)

            self.conversation_history.append({
                "role": "user",
                "content": student_question,
                "type": question_type,
                "course": course_name
            })

            if question_type == "exercise":
                type_instruction = """Provide 2-3 practice problems related to this course topic. Make them progressively harder. Include:
                                    - Problem statement in plain text
                                    - Expected approach or solution hints
                                    - Difficulty level (Easy/Medium/Hard)
                                    Problems must be appropriate for the course."""
                
            elif question_type == "resources":
                type_instruction = """Provide 2-4 legitimate educational links about the topic. Include a brief explanation for each.
                                    Allowed sources: Khan Academy, Wikipedia, GeeksforGeeks, Visualgo, YouTube educational channels, GitHub repositories.
                                    Only provide links relevant to the course topic."""
                
            elif question_type == "notes":
                type_instruction = """Provide clear, well-organized notes in plain text.
                                    Include main points, definitions, and key ideas.
                                    Use line breaks to separate ideas. No symbols, bullets, or markdown."""
                
            else:  
                type_instruction = """Provide a clear, intermediate-level explanation.
                                    Include:
                                    - Simple definition of the topic
                                    - How it works with a practical example
                                    - Why it matters in this course
                                    Keep explanations plain text, natural, and conversational."""

            system_prompt = f"""You are an educational assistant for the course: {course_name}

                                {type_instruction}

                                RESPONSE FORMAT RULES:
                                - Plain text ONLY
                                - No asterisks (*), hash marks (#), underscores (_), bullets, or code fences
                                - Use simple line breaks to separate paragraphs
                                - Keep tone friendly and supportive
                                - Provide visualization links [VISUALIZATION: name - url] only if truly helpful

                                BEHAVIOR RULES:
                                - Answer questions related to {course_name}
                                - If the question is unrelated to this course, respond: "This question is not related to {course_name}."
                                - Be helpful, clear, and concise"""

            user_prompt = f"""COURSE: {course_name}
                            STUDENT QUESTION: {student_question}

                            INSTRUCTIONS:
                            - Provide a complete, plain text answer
                            - Keep response appropriate for the course level
                            - Approximate length: {max_tokens} tokens"""

            response = self.client.chat.completions.create(
                model="google/gemini-2.5-flash-lite",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )

            answer = response.choices[0].message.content
            

            return answer

        except ValueError as e:
            return "Sorry, there was a problem processing your question. Please try again."
        except Exception as e:
            print(f"Warning: Error processing question: {e}")
            return "Sorry, there was a problem processing your question. Please try again."

class QuestionChecker:
        def __init__(self):
            self.client = getAPI()
        
        def check(self, question:str, course, sample_outputs="not provided", restrctions="not provided"):
            if not question.strip():
                return {"correct":False, "message":"Qustion should not be empty"}
            
            system_prompt="""You are a Quiz Validation AI. 
                            Your task is to check whether the provided quiz question, sample output, and course restriction are logically consistent and suitable for quiz creation.

                            Given:
                            - course_name: the course the quiz belongs to
                            - question: the quiz question text
                            - sample_output: the expected example answer(if not provided, suggest sample_output)
                            - restriction: any constraints (e.g., data types, allowed operations, input limits)

                            You must analyze the following:

                            1. **Course Relevance**  
                            - Check if the question is related to the course.  
                            Example: If course = "Mathematics" but the question is about "Python programming", then it's invalid.

                            2. **Question–Output Alignment**  
                            - Check if the sample output is realistic and logically possible given the question.
                            - Detect contradictions, impossible outputs, missing steps, or wrong formats.

                            3. **Restriction Compatibility**  
                            - Check if the question and sample output follow the stated restrictions.
                            - If restrictions contradict the question/output (e.g., "no loops allowed" but the task requires loops), mark invalid.

                            4. **Quality Check**  
                            - Identify minor issues such as grammar mistakes, unclear wording, or missing information.

                            ### ✅ Required Response Format

                            Respond strictly in this format:
                            [True, suggestions] If everything is valid.
                            Or:
                            [False, explanation or suggestions]
                            Where suggestions may include:
                            - wrong course
                            - wrong or impossible sample output
                            - mismatch between question and output
                            - unclear question
                            - violation of restriction
                            - minor mistakes detected
                            ### The response must always be:
                            [boolean, suggestion]
                            """
                            
                            
            user_prompt=f"""course_name : {course}
                            question :{question} 
                            sample_output:{sample_outputs}
                            restrictions : {restrctions}"""
                            
            response = self.client.chat.completions.create(
                        model="google/gemini-2.5-flash-lite",
                        messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                        temperature=0.7,
                        max_tokens=100
                )
            
            raw = response.choices[0].message.content.strip()

            match = re.match(r"\[(True|False)\s*,\s*(.*)\]", raw, re.DOTALL)
                
            if match:
                is_correct = match.group(1) == "True"
                message = match.group(2)
            else:
                is_correct = False
                message = "AI API was busy"

            return {"correct": is_correct, "message": message}
        
