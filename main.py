import os
import tempfile
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from openai import OpenAI
from supabase import create_client, Client

app = FastAPI()

# Initialize AI client for Groq using environment variables
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Supabase Credentials Configuration using environment variables
SUPABASE_URL = "https://dlizbqvysbrzbihtwkjs.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        username = data.get("username", "Anonymous")
        message = data.get("message", "")

        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Iris, a helpful and friendly AI assistant."},
                {"role": "user", "content": message}
            ]
        )
        reply = response.choices[0].message.content

        # Log to Supabase Storage
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_content = f"[{datetime.now(timezone.utc).isoformat()}] {username}: {message}\n[Iris]: {reply}\n\n"
        
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
            tmp.write(log_content)
            tmp_path = tmp.name

        file_path_in_bucket = f"{username}/logs/chat_log_{today}.txt"
        
        with open(tmp_path, "rb") as f:
            try:
                supabase.storage.from_("AIN Cloud Storage").upload(
                    path=file_path_in_bucket,
                    file=f,
                    file_options={"upsert": "true"}
                )
            except Exception as upload_err:
                print(f"Supabase upload warning: {upload_err}")

        os.unlink(tmp_path)

        return {"reply": reply}
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

