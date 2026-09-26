import os
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional


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


class AuthCredentials(BaseModel):
    email: str = None
    password: str = None


@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        return {"user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def login(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": response.user
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid login credentials")
@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def profile(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    token = authorization.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401, detail="Access token required")
    return {"message": "token present, not yet verified"}