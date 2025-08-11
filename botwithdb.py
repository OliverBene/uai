import os
import firebase as pyrebase
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from datetime import datetime
import pytz
import uuid

# --------------------------
# 1. ENV + GPT INIT
# --------------------------
load_dotenv()

client = OpenAI(api_key="API_KEY")  # Replace with real key or load from env

firebaseConfig = {
    "apiKey": "API_KEY_TO_BE_REPLACED",
    "authDomain": "AUTH_DOMAIN_URL_TO_BE_REPLACED",
    "databaseURL": "DATABASE_URL_TO_BE_REPLACED",
    "projectId": "PROJECT_ID_TO_BE_REPLACED",
    "storageBucket": "STORAGE_BUCKET_TO_BE_REPLACED",
    "messagingSenderId": "MESSENGER_SENDER_ID_TO_BE_REPLACED",
    "appId": "APP_ID__TO_BE_REPLACED",
    "measurementId": "MEASUREMENT_ID_TO_BE_REPLACED"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

app = FastAPI(
    title="CS AI Assistant (Realtime DB)",
    description="Specialized AI for Computer Science Students - Firebase Version",
    version="1.1"
)

# --------------------------
# 2. DATA MODELS
# --------------------------
class User(BaseModel):
    id: str
    name: str
    matric_no: str
    year: int
    courses: List[str]
    query_count: int = 0

class CSQuestion(BaseModel):
    question: str
    response: Optional[str] = None
    timestamp: Optional[datetime] = None
    course_code: Optional[str] = None
    user_id: str

# --------------------------
# 3. DB UTILS
# --------------------------
class FirebaseDB:
    @staticmethod
    def get_user(uid: str) -> Optional[User]:
        data = db.child("users").child(uid).get().val()
        if not data:
            return None
        return User(
            id=uid,
            name=data.get("name", ""),
            matric_no=data.get("matric_no", ""),
            year=int(data.get("year", 1)),
            courses=list(data.get("courses", {}).keys()),
            query_count=int(data.get("query_count", 0))
        )

    @staticmethod
    def update_query_count(uid: str, count: int):
        db.child("users").child(uid).update({"query_count": count})

    @staticmethod
    def get_course(code: str) -> Optional[dict]:
        return db.child("courses").child(code.upper()).get().val()

    @staticmethod
    def log_question(uid: str, q: CSQuestion):
        q_id = str(uuid.uuid4())
        data = {
            "question": q.question,
            "response": q.response,
            "timestamp": q.timestamp.isoformat(),
            "course_code": q.course_code or ""
        }
        db.child("questions").child(uid).child(q_id).set(data)

# --------------------------
# 4. AI LOGIC
# --------------------------
class CSAIEngine:
    CS_CONTEXT = """
    You are a Osun State University Computer Science assistant. Specialize in:
    - Programming (Python/Java/C++)
    - Algorithms
    - Data Structures
    - Courses like CSC101, CSC201, MTH101, MTH102, PHY101, PHY102, CHM101, CHM102
    
    Department Info:
    - HOD: Dr. Jimoh
    - Lab: Mon/Wed 10am-4pm
    - Contact: csdept@uniosun.edu.ng
    """

    @staticmethod
    def generate_cs_response(query: str, user: User) -> str:
        course = next((c for c in user.courses if c.lower() in query.lower()), None)
        if course:
            course_info = FirebaseDB.get_course(course)
            if course_info:
                return f"{course} ({course_info['title']}): {course_info.get('next_topic', 'Ask your lecturer')}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": CSAIEngine.CS_CONTEXT},
                    {"role": "user", "content": f"CS Student ({user.year} year) asks: {query}"}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(503, f"AI Error: {str(e)}")

# --------------------------
# 5. API ENDPOINTS
# --------------------------
@app.post("/cs/ask")
async def ask_cs_question(request: CSQuestion):
    user = FirebaseDB.get_user(request.user_id)
    if not user:
        raise HTTPException(404, "CS student not found in database")

    if user.query_count >= 50:
        raise HTTPException(429, "Daily limit reached")

    response = CSAIEngine.generate_cs_response(request.question, user)
    now = datetime.now(pytz.timezone("Africa/Lagos"))

    FirebaseDB.log_question(user.id, CSQuestion(
        question=request.question,
        response=response,
        timestamp=now,
        user_id=user.id,
        course_code=request.course_code
    ))

    FirebaseDB.update_query_count(user.id, user.query_count + 1)

    return {"response": response}

@app.get("/cs/courses/{code}")
async def get_cs_course(code: str):
    course = FirebaseDB.get_course(code)
    if not course:
        raise HTTPException(404, "Course not found")
    return course

# --------------------------
# 6. LEGACY MOCK DB (Commented Out)
# --------------------------
"""
class MockDB:
    users = {
        "CS_STUDENT_1": User(
            id="CS_STUDENT_1",
            name="Test Student",
            matric_no="CS2023001",
            year=2,
            courses=["CSC101", "CSC201"]
        )
    }

    courses = {
        "CSC101": {"title": "Intro to Programming", "lecturer": "Dr. Smith", "next_topic": "Recursion", "lab_schedule": "Tues 2-4"},
        "CSC201": {"title": "Data Structures", "lecturer": "Dr. Johnson", "next_topic": "Binary Trees", "lab_schedule": "Thurs 10-12"}
    }

    questions = []

    @classmethod
    def get_user(cls, user_id: str): return cls.users.get(user_id)
    @classmethod
    def get_course(cls, code: str): return cls.courses.get(code.upper())
    @classmethod
    def log_question(cls, question: CSQuestion): cls.questions.append(question)
"""

# --------------------------
# 7. LOCAL DEV SERVER
# --------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
