import database
from models import Professor

def addTestData():
    database.open_database()
    python_prof=Professor.Professor(111, "Dr.Visit Hirankitti")
    python_prof.create_course("Python", "/data/python")
    python_prof.create_quiz("""Find the first non-repeating character in a string.
                    Return its index. If it doesn’t exist, return -1.
                    Example:
                    Input: "leetcode"
                    Output: 0
                    Explanation: 'l' is the first non-repeating character.""","""def firstUniqChar(s):
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

                    """,5,"none")
    
    database.root.professors[111]=python_prof
    database.update_database()
    database.close_database()