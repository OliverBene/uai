import firebase as pyrebase

# Firebase config
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

# Add dummy user
user_id = "CS_STUDENT_1"
user_data = {
    "name": "Test Student",
    "matric_no": "CS2023001",
    "year": 2,
    "query_count": 0,
    "courses": {
        "CSC101": True,
        "CSC201": True
    }
}
db.child("users").child(user_id).set(user_data)
print(f"✅ Added user {user_id}")

# Add dummy courses
courses = {
    "CSC101": {
        "title": "Introduction to Programming",
        "lecturer": "Dr. Smith",
        "next_topic": "Recursion",
        "lab_schedule": "Tuesdays 2-4pm"
    },
    "CSC201": {
        "title": "Data Structures",
        "lecturer": "Dr. Johnson",
        "next_topic": "Binary Trees",
        "lab_schedule": "Thursdays 10am-12pm"
    }
}

for code, details in courses.items():
    db.child("courses").child(code).set(details)
    print(f"✅ Added course {code}")

# (Optional) Display inserted data
print("\n🔎 Fetching user data:")
print(db.child("users").child(user_id).get().val())

print("\n🔎 Fetching course CSC101:")
print(db.child("courses").child("CSC101").get().val())
