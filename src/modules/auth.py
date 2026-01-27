import json
import os
import re
import bcrypt
import streamlit as st

# --- CONFIGURATION ---
USER_DB_FILE = "users_db.json"
CHAT_DIR = "chat_history"

# --- ADMIN CREDENTIALS ---
ADMIN_USERNAME = "BenHua"
ADMIN_PASSWORD = "123456Admin"

# --- SECURITY QUESTIONS LIBRARY ---
SECURITY_QUESTIONS_LIBRARY = [
    "What is the name of your first pet?",
    "In what city were you born?",
    "What is your mother's maiden name?",
    "What was the make of your first car?",
    "What is the name of your favorite teacher?",
    "What is your favorite food?",
    "What represents your favorite color?",
    "Where did you go for your first vacation?",
    "What is the name of the street you grew up on?",
    "What is your childhood nickname?"
]

# --- INITIALIZATION ---
if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r") as f:
        return json.load(f)

# --- VALIDATION FUNCTIONS ---
def validate_username(username):
    # --- Returns True if username contains only letters and numbers ---
    if re.match(r'^[a-zA-Z0-9]+$', username):
        return True
    return False

def validate_password(password):
    # --- Returns True if password is >= 6 chars AND contains at least one letter ---
    if len(password) < 6:
        return False
    if not any(char.isalpha() for char in password):
        return False
    return True

# --- HELPER: HASHING ---
def hash_text(text):
    """Hashes a text (password or security answer) using bcrypt."""
    return bcrypt.hashpw(text.strip().lower().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_hash(plain_text, hashed_text):
    """Checks if plain text matches the hash."""
    return bcrypt.checkpw(plain_text.strip().lower().encode('utf-8'), hashed_text.encode('utf-8'))

# --- AUTHENTICATION FUNCTIONS ---
def is_admin(username):
    """Checks if the logged-in user is the admin."""
    return username == ADMIN_USERNAME

def save_user(username, password, security_questions=None):
    """
    Saves a new user with password and optional security questions.
    """
    users = load_users()
    if username in users:
        return False  # User already exists

    # --- Process Security Questions (Hash the answers) ---
    processed_questions = []
    if security_questions:
        for item in security_questions:
            processed_questions.append({
                "question": item['question'],
                "answer_hash": hash_text(item['answer'])
            })

    users[username] = {
        "password": hash_text(password),
        "security_questions": processed_questions
    }
    
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)
    return True

def verify_login(username, password):
    # --- 1. Check for Admin Hardcoded Login ---
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True

    # --- 2. Check Standard Users ---
    users = load_users()
    if username in users:
        user_data = users[username]
        
        # --- Handle Legacy (String) vs New (Dict) ---
        if isinstance(user_data, str):
            # --- Old format ---
            stored_hash = user_data
        elif isinstance(user_data, dict):
            # --- New format ---
            stored_hash = user_data.get("password")
        else:
            return False
            
        return check_hash(password, stored_hash)
    
    return False

# --- PASSWORD MANAGEMENT FUNCTIONS ---
def get_security_questions(username):
    """Returns the list of questions for a user (without answers)."""
    users = load_users()
    user_data = users.get(username)
    
    # --- Check if user exists AND has the new dictionary format AND has questions ---
    if user_data and isinstance(user_data, dict) and "security_questions" in user_data:
        return [q['question'] for q in user_data['security_questions']]
    
    return None

def verify_security_answers(username, answers_list):
    """Verifies a list of answers against the stored hashes."""
    users = load_users()
    user_data = users.get(username)
    
    # --- Validate user data structure ---
    if not user_data or not isinstance(user_data, dict) or "security_questions" not in user_data:
        return False

    stored_qs = user_data["security_questions"]
    
    if len(answers_list) != len(stored_qs):
        return False

    # --- Check each answer ---
    for i, provided_answer in enumerate(answers_list):
        if not check_hash(provided_answer, stored_qs[i]["answer_hash"]):
            return False
            
    return True

def reset_password(username, new_password):
    """Updates the user's password (Used by Forgot Password Page)."""
    users = load_users()
    if username in users:
        # --- Preserve existing data structure if it's a dictionary ---
        if isinstance(users[username], dict):
            users[username]["password"] = hash_text(new_password)
        else:
            # --- Upgrade legacy string user to dictionary format ---
            users[username] = {
                "password": hash_text(new_password),
                "security_questions": []
            }
            
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f)
        return True
    return False

def change_password(username, new_password):
    """
    Updates the user's password (Used by Sidebar).
    Reuses the robust logic from reset_password.
    """
    return reset_password(username, new_password)

# --- USER MANAGEMENT ---
def get_all_users():
    return load_users()

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f)
    
    # --- Delete history files ---
    history_file = os.path.join(CHAT_DIR, f"{username}_interaction.jsonl")
    if os.path.exists(history_file):
        os.remove(history_file)

    session_file = os.path.join(CHAT_DIR, f"{username}_session_state.pkl")
    if os.path.exists(session_file):
        os.remove(session_file)        
    
    return True

def get_user_history_file(username):
    return os.path.join(CHAT_DIR, f"{username}_history.json")