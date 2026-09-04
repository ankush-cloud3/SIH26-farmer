import os
import random
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Mandipaye B2B Wholesale Marketplace API")

# --- 1. ALLOW CORS FOR GITHUB PAGES & LOCAL DEV ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from GitHub Pages, localhost, and Render
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. SUPABASE & AUTH ENGINE CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set in server/.env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Password Hashing Engine using Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- 3. PYDANTIC REQUEST & RESPONSE MODELS ---
class SignupRequest(BaseModel):
    phone_number: str = Field(..., example="9876543210")
    password: str = Field(..., min_length=6)

class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp: str

class SigninRequest(BaseModel):
    phone_number: str
    password: str

class Listing(BaseModel):
    id: Optional[str] = None
    title: str
    category: str
    price_per_kg: float
    moq_kg: int
    available_stock_kg: int
    pincode: str


# --- 4. HELPER FUNCTIONS ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_otp() -> str:
    return str(random.randint(100000, 999999))


# --- 5. AUTHENTICATION ENDPOINTS ---

@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    # Check if user already exists
    existing = supabase.table("users").select("*").eq("phone_number", req.phone_number).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Phone number already registered. Please sign in.")

    # Hash the password & generate OTP
    hashed_pwd = hash_password(req.password)
    otp = generate_otp()

    # Save user record in Supabase
    user_payload = {
        "phone_number": req.phone_number,
        "hashed_password": hashed_pwd,
        "otp_code": otp,
        "is_verified": False
    }
    
    supabase.table("users").insert(user_payload).execute()

    # Console output for testing before Twilio integration
    print(f"--- DEMO OTP GENERATED FOR +91 {req.phone_number}: {otp} ---")

    return {
        "message": "Account created successfully. Verification code dispatched.",
        "phone_number": req.phone_number,
        "demo_otp": otp
    }


@app.post("/api/auth/verify-otp")
def verify_otp(req: VerifyOtpRequest):
    user_res = supabase.table("users").select("*").eq("phone_number", req.phone_number).execute()
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User account not found.")

    user = user_res.data[0]

    if user["otp_code"] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code entered.")

    # Update account status to active & invalidate OTP
    supabase.table("users").update({"is_verified": True, "otp_code": None}).eq("phone_number", req.phone_number).execute()

    return {"message": "Mobile number verified successfully! You can now sign in."}


@app.post("/api/auth/signin")
def signin(req: SigninRequest):
    user_res = supabase.table("users").select("*").eq("phone_number", req.phone_number).execute()
    if not user_res.data:
        raise HTTPException(status_code=400, detail="Invalid phone number or password.")

    user = user_res.data[0]

    # Check hashed password
    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid phone number or password.")

    # Check verification status
    if not user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Account not verified. Please verify your OTP.")

    return {
        "message": "Login successful!",
        "user": {
            "id": user["id"],
            "phone_number": user["phone_number"]
        }
    }


# --- 6. MARKETPLACE PRODUCE ENDPOINTS ---

@app.get("/api/listings")
def get_listings(mode: Optional[str] = "bulk_buyer"):
    query = supabase.table("listings").select("*")
    
    # Mandatory Bulk Sourcing Filter Logic
    if mode == "bulk_buyer":
        query = query.gte("moq_kg", 100)
    elif mode == "retailer":
        query = query.lt("moq_kg", 100)
        
    res = query.execute()
    return res.data


@app.get("/")
def health_check():
    return {"status": "online", "system": "Mandipaye B2B API Engine"}