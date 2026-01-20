from openai import OpenAI
from dotenv import load_dotenv
import os
import streamlit as st

# Load environment variables (for local .env files if you use them)
load_dotenv()

# Initialize variables
api_key = None
base_url = None
model = None

# --- HYBRID CONFIGURATION ---

# 1. Try to get API Key from Streamlit Secrets (Cloud)
# We wrap this in a try-except block because accessing st.secrets crashes 
# if no secrets.toml file exists locally.
try:
    if "GROQ_API_KEY" in st.secrets:
        print("☁️ Detected Cloud Environment: Using Groq API")
        api_key = st.secrets["GROQ_API_KEY"]
        base_url = "https://api.groq.com/openai/v1"
        model = "llama3-8b-8192"
except Exception:
    # If secrets file is missing, we just ignore it and fall through to local checks
    pass

# 2. If we didn't find cloud keys, check local .env
if api_key is None:
    if os.getenv("GROQ_API_KEY"):
        # --- LOCAL HYBRID MODE (Local laptop using Cloud API) ---
        print("☁️ Detected Local .env Key: Using Groq API")
        api_key = os.getenv("GROQ_API_KEY")
        base_url = "https://api.groq.com/openai/v1"
        model = "llama3-8b-8192"

    else:
        # --- LOCALHOST MODE (Offline / LM Studio) ---
        print("💻 No Cloud Keys found: Using Localhost (LM Studio)")
        api_key = "lm-studio"
        base_url = "http://localhost:1234/v1"
        # LM Studio uses whatever model is currently loaded
        model = "local-model"

# --- INITIALIZE CLIENT ---
client = OpenAI(
    base_url=base_url,
    api_key=api_key
)

# --- DIRECTORY SETUP ---
# Create a directory for saving the chat history if it doesn't exist
if not os.path.exists("chat_history"):
    os.makedirs("chat_history")

chat_history_path = "chat_history/"