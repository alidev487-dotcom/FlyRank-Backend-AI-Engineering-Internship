import os
from fastapi import FastAPI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Auth API",
    description="A secure API with Supabase authentication.",
    version="1.0"
)

print("Server running and connected to Supabase")

@app.get("/")
def read_root():
    return {"message": "Server running and connected to Supabase"}