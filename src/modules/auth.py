import json
import os
import re
import bcrypt
import streamlit as st

# --- CONFIGURATION ---
# Stores username and hashed passwords
USER_DB_FILE = "users_db.json"
# Directory where chat logs and session states are stored
CHAT_DIR = "chat_history"

# --- ADMIN CREDENTIALS ---
ADMIN_USERNAME = "BenHua"
ADMIN_PASSWORD = "123456Admin"

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
    # --- Returns True if username contains only letters and numbers (no special chars). ---
    if re.match(r'^[a-zA-Z0-9]+$', username):
        return True
    return False

def validate_password(password):
    # --- Returns True if password is >= 6 chars AND contains at least one letter. ---
    if len(password) < 6:
        return False
    if not any(char.isalpha() for char in password): # --- Check for at least one letter ---
        return False
    return True

# --- AUTHENTICATION FUNCTIONS ---
def save_user(username, password):
    """
    Saves a new user with a hashed password using bcrypt.
    """
    users = load_users()
    
    # --- Check if user already exists or tries to register as Admin ---
    if username in users or username == ADMIN_USERNAME:
        return False
    
    # --- Hash the password before saving ---
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users[username] = hashed
    
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)
    return True

def verify_login(username, password):
    """
    Verifies login for both Admin and Regular Users using bcrypt.
    """
    # --- 1. Check Admin Login ---
    if username == ADMIN_USERNAME:
        return password == ADMIN_PASSWORD

    # --- 2. Check Regular User Login ---
    users = load_users()
    if username in users:
        stored_hash = users[username]
        # --- Verify the provided password against the stored hash ---
        # --- Handle cases where old passwords might be plain text ---
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except ValueError:
            # --- Fallback if we have old plain text passwords in our DB ---
            return stored_hash == password
            
    return False

def change_password(username, new_password):
    users = load_users()
    if username in users:
        # --- Hash the NEW password ---
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users[username] = hashed
        
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f)
        return True
    return False

# --- ADMIN FUNCTIONS ---
def is_admin(username):
    """Check if the current user is the admin."""
    return username == ADMIN_USERNAME

def get_all_users():
    """
    Returns a dictionary of all users so the admin can view them.
    """
    return load_users()

def delete_user(username):
    """
    Deletes the user's credentials and their specific chat history files.
    """
    # --- 1. Remove from User DB ---
    users = load_users()
    if username in users:
        del users[username]
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f)
    
    # --- 2. Delete Chat History File (JSONL) ---
    # --- Matches the path used in wildfireChat.py ---
    history_file = os.path.join(CHAT_DIR, f"{username}_interaction.jsonl")
    if os.path.exists(history_file):
        os.remove(history_file)

    # --- 3. Delete Session State File (Pickle) ---
    # --- Matches the path used in wildfireChat.py ---
    session_file = os.path.join(CHAT_DIR, f"{username}_session_state.pkl")
    if os.path.exists(session_file):
        os.remove(session_file)        
    
    return True

# --- HISTORY HELPERS (Preserved) ---
def get_user_history_file(username):
    return os.path.join(CHAT_DIR, f"{username}_history.json")

def load_chat_history(username):
    filepath = get_user_history_file(username)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

def save_chat_history(username, history):
    filepath = get_user_history_file(username)
    with open(filepath, "w") as f:
        json.dump(history, f)