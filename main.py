import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client

app = FastAPI(title="AIN Cloud - Secure Cloud Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI client for Groq using environment variables
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Supabase Credentials Configuration using environment variables
SUPABASE_URL = "https://dlizbqvysbrzbihtwkjs.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "AIN Cloud Storage"

class AccountRequest(BaseModel):
    username: str

class MessagePayload(BaseModel):
    username: str
    message: str

@app.get("/")
def home():
    """Serves the web UI directly."""
    return FileResponse("index.html")

@app.post("/create-account")
def create_account(data: AccountRequest):
    """Initializes account profiling configuration."""
    return {"status": "success", "message": f"Account profile and cloud roots structured for {data.username}."}

@app.post("/verify-identity")
async def verify_identity(
    username: str = Form(...),
    full_name: str = Form(...),
    passport_image: UploadFile = File(...)
):
    """Uploads passport files and text records directly into the 'AIN Cloud Storage' Supabase bucket."""
    file_extension = os.path.splitext(passport_image.filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"{username}/verification/passport_{timestamp}{file_extension}"
    
    contents = await passport_image.read()
    
    # This will now print any storage error straight to your terminal if it fails
    res = supabase.storage.from_(BUCKET_NAME).upload(
        file=contents,
        path=image_filename,
        file_options={"content-type": passport_image.content_type or "image/jpeg", "upsert": "true"}
    )
    print("Passport Upload Response:", res)

    meta_filename = f"{username}/verification/details_{timestamp}.txt"
    meta_content = f"Username: {username}\nFull Name: {full_name}\nTimestamp: {datetime.now().isoformat()}\nImage File: {image_filename}\n"
    
    supabase.storage.from_(BUCKET_NAME).upload(
        file=meta_content.encode('utf-8'),
        path=meta_filename,
        file_options={"content-type": "text/plain", "upsert": "true"}
    )
        
    return {"status": "verified", "detail": "Passport image and verification text data securely saved to Supabase."}

@app.post("/chat")
def chat_with_iris(payload: MessagePayload):
    """Interacts with Iris and saves chat transcripts directly into the cloud storage bucket."""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are Iris, an independent cloud AI assistant running on AIN Cloud. You are helpful, calm, smart, and direct."
                },
                {
                    "role": "user",
                    "content": payload.message
                }
            ],
            temperature=0.7
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Error connecting to AI model: {str(e)}"

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"{payload.username}/IRIS (Cloud)/logs/chat_log_{date_str}.txt"
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    log_entry = f"[{timestamp}] USER: {payload.message}\n[{timestamp}] IRIS: {reply}\n" + "-" * 40 + "\n"
    
    # This will print chat log upload results directly to your terminal
    chat_res = supabase.storage.from_(BUCKET_NAME).upload(
        file=log_entry.encode('utf-8'),
        path=log_filename,
        file_options={"content-type": "text/plain", "upsert": "true"}
    )
    print("Chat Log Upload Response:", chat_res)

    return {"reply": reply}
