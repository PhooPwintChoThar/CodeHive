from openai import OpenAI
import os

def getAPI():
    return OpenAI(
            api_key="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",  # Replace with: sk-or-v1-xxxxx
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
        if not all([question , reference_code, student_code]):
            raise ValueError("Answer code should not be empty!")
        
        return f"""You are an expert {language} programming instructor evaluating student code submissions.
                    Question:{question}, 
                    Reference Solution:{reference_code}, 
                    Student's submission{student_code}.
                    Your task is to evaluate if the student's code {student_code} correctly solves the problem.Remember:
                    
                    1.Different approaches and implementations are acceptable if they solve the problem correctly
                    2.Focus on correctness, logic, and whether it meets the requirements
                    3.The solution must not include of use the tech stacks : {restricted_things} (if None any stack can use)
                    4.You need to score strictly if it fullfills none of the requirement, then score 0 
                    5.provide mistakes for every score less than full score
                    Please provide your evaluation in the following format:
                    [Score: Give a score from 0 - {total_score}]#[mistake1],[mistake2]etc#[comment](only if the solution fullfils the requirement but includes some informal cases that you are not sure it should be reduced scores)
                    You don't need to give any extr word except above format
                    """
                    
    def evaluate_code(self, question:str, reference_code:str,student_code:str,  language:str, restricted_things:str=None, total_score:int=10):
            if not all([question , reference_code, student_code]):
                raise ValueError("Answer code should not be empty!")
            
            
            try:
                evaluation_prompt=self.create_prompt(question, reference_code,student_code,language,restricted_things,total_score)
                response = self.client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",  # Latest Gemini 2.0 - Best free model!
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
                #score=[0],mistakes=[1];comment=[2]
                response_data=response.choices[0].message.content.split("#")
                
                while(len(response_data)<3):
                    response_data.append(None)
                return response_data
            except Exception as e:
                raise RuntimeError(f"Error in processing prompt : {e}")
        

class TeacherAssistant:
    def __init__(self):
        self.client = getAPI()
        self.conversation_history = []
        
    def _get_lecture_content(self, filepath: str) -> str:
        if os.path.isdir(filepath):
            all_text = ""
            txt_files = [f for f in os.listdir(filepath) if f.lower().endswith('.txt')]
            
            if not txt_files:
                raise ValueError(f"No TXT files found in directory: {filepath}")
            
            for txt_file in sorted(txt_files):
                txt_path = os.path.join(filepath, txt_file)
                try:
                    with open(txt_path, 'r', encoding='utf-8') as file:
                        text = file.read()
                    all_text += f"\n\n--- From {txt_file} ---\n{text}"
                except Exception as e:
                    print(f"Warning: Could not read {txt_file}: {e}")
            
            return all_text
        
        elif filepath.lower().endswith('.txt'):
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"TXT file not found: {filepath}")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    return file.read()
            except Exception as e:
                raise RuntimeError(f"Error reading TXT file: {e}")
        
        else:
            raise ValueError("Filepath must point to a TXT file or directory containing TXT files")  
        
    def _detect_question_type(self, question):
        question_lower = question.lower()
        exercise_keywords = ["exercise", "practice",  "challenge", "task"]
        
        if any(keyword in question_lower for keyword in exercise_keywords):
            return "exercise"
        else:
            return "explanation"
    
    def _calculate_dynamic_max_tokens(self, question: str, question_type: str) -> int:
        question_length = len(question.split())
        base_tokens = 300
        
        if question_type == "exercise":
            base_tokens = 500
        elif question_type == "explanation":
            base_tokens = 400
        
        if question_length > 50:
            base_tokens += 150
        elif question_length > 30:
            base_tokens += 75
        
        return min(base_tokens, 1200)
    
    def chat(self, student_question, lecture_filepath):
        if not student_question or not student_question.strip():
            raise ValueError("Question cannot be empty!")
        
        try:
            lecture_content = self._get_lecture_content(lecture_filepath)
            
            question_type = self._detect_question_type(student_question)
            
            
            max_tokens = self._calculate_dynamic_max_tokens(student_question, question_type)
            
            self.conversation_history.append({
                "role": "user",
                "content": student_question,
                "type": question_type
            })
            
            if question_type == "exercise":
                type_instruction = """Provide 2-3 practice problems directly related to the lecture topics. Make them progressively harder. Include:
                Problem statement in plain text
                Expected approach or solution hints
                Difficulty level (Easy/Medium/Hard)
                You can use problems from outside the lectures but they MUST align with what was taught."""
            else:
                type_instruction = """
            Explain the concept using ONLY plain text. Include:

            A simple definition of the topic
            How it works with a concrete example from the lecture
            Why it matters or when to use it
            Use natural language without any markdown formatting.

            VISUALIZATION LINKS:
            If a visualization would significantly help understanding the concept, include one open-source resource link in this format:
            [VISUALIZATION: concept_name - url_to_resource]          
            Examples of resources to link:

            Khan Academy: https://www.khanacademy.org/
            Wikipedia diagrams and animations
            GeeksforGeeks visualizations: https://www.geeksforgeeks.org/
            Visualgo algorithm visualizations: https://visualgo.net/
            YouTube educational videos
            GitHub educational repositories with diagrams

            Only include links to legitimate, free, educational resources."""
            
            # Create system prompt
            system_prompt = f"""You are an educational assistant that explains concepts clearly and simply.

                {type_instruction}

                RESPONSE FORMAT RULES:

                Write in plain text ONLY
                No asterisks (*), hash marks (#), underscores (_), or backticks (`)
                No bullet points or numbered lists with symbols
                No markdown code blocks
                Use simple line breaks to separate paragraphs
                If showing code, write it as plain text lines
                Keep explanations natural and conversational
                Only include [VISUALIZATION: name - url] tags when truly helpful

                Core Guidelines:

                Use only information from the lecture materials
                If not in lectures, say "This topic is not covered in the provided lecture materials"
                Be clear and direct
                Support claims with examples from the lecture
                Keep response complete and well-organized
                Be encouraging and helpful
                Provide visualization links only when they significantly enhance understanding"""
            
    
            user_prompt = f"""LECTURE CONTENT:
                            {lecture_content}
                            STUDENT QUESTION:
                            {student_question}
                            IMPORTANT:

                            Answer only using the lecture content above
                            Write in plain text with no special formatting
                            Keep it clear and straightforward
                            Complete your full answer in approximately {max_tokens} tokens"""
            
            response = self.client.chat.completions.create(
                    model="google/gemini-2.0-flash-exp:free",
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
                    max_tokens=max_tokens
                )
            return response.choices[0].message.content
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Lecture file error: {e}")
        except ValueError as e:
            raise ValueError(f"Input error: {e}")
        except Exception as e:
            raise RuntimeError(f"Error processing question: {e}")

        
