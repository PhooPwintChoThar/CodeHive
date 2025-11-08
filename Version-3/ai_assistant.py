from openai import OpenAI

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
                return response_data
            except Exception as e:
                raise RuntimeError(f"Error in processing prompt : {e}")
        
        