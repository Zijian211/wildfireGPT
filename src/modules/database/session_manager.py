import streamlit as st
import pickle
import os
import sys

# --- Fix Imports for robustness ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.assistants.assistant_router import AssistantRouter

# Directory for saving sessions
HISTORY_DIR = "chat_history"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def get_session_file_path(username):
    return os.path.join(HISTORY_DIR, f"{username}_session_state.pkl")

def save_user_session(username):
    """
    Saves ONLY data (Messages, Persona, Location). 
    Does NOT save the 'assistant' object to avoid pickle crashes on code updates.
    """
    file_path = get_session_file_path(username)
    
    # --- 1. Pack ONLY Data ---
    state_data = {
        "messages": st.session_state.get("messages", []),
        "location_confirmed": st.session_state.get("location_confirmed", False),
        "lat": st.session_state.get("lat"),
        "lon": st.session_state.get("lon"),
        "user_persona": st.session_state.get("user_persona", "👨‍🚒 Emergency Commander (Gov)")
    }
    
    try:
        # Use temporary file to avoid corruption
        temp_file = file_path + ".tmp"
        with open(temp_file, "wb") as f:
            pickle.dump(state_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        # Atomic replace
        os.replace(temp_file, file_path)
        print(f"✅ Session saved for {username}: {len(state_data['messages'])} messages")
    except Exception as e:
        print(f"❌ Save failed for {username}: {e}")
        # Try one more time with basic protocol
        try:
            with open(file_path, "wb") as f:
                pickle.dump(state_data, f, protocol=2)
        except:
            pass

def load_user_session(username):
    """
    Loads data and RE-INITIALIZES the Assistant.
    """
    # 1. Check if data is already in memory to avoid constant reloading
    if st.session_state.get("data_loaded", False):
        return

    file_path = get_session_file_path(username)
    
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
                
                # --- 2. Restore Simple Data ---
                st.session_state.messages = data.get("messages", [])
                st.session_state.location_confirmed = data.get("location_confirmed", False)
                st.session_state.lat = data.get("lat", -33.8688)
                st.session_state.lon = data.get("lon", 151.2093)
                
                # Restore Persona
                saved_persona = data.get("user_persona", "👨‍🚒 Emergency Commander (Gov)")
                st.session_state.user_persona = saved_persona

                # --- 3. RE-CREATE Assistant (The Fix) ---
                # We must pass the AGENT NAME (e.g., "ChecklistAssistant"), NOT the PERSONA.
                # The Persona is handled separately by the Context Manager.
                st.session_state.assistant = AssistantRouter("ChecklistAssistant")

            print(f"✅ Session loaded for {username}: {len(st.session_state.messages)} messages")
            st.toast("✅ Session restored.")
        else:
            # New User or No File
            print(f"⚠️ No session file found for {username}, initializing defaults")
            init_defaults()
            
    except Exception as e:
        # If loading fails (e.g. old corrupt file), force a reset so the app works
        print(f"❌ Error loading session for {username}: {e}")
        st.error("⚠️ Session file was incompatible. Starting fresh.")
        init_defaults()

    # 4. Mark as loaded
    st.session_state.data_loaded = True

def init_defaults():
    """
    Sets the default state for a new session.
    """
    st.session_state.messages = []
    st.session_state.location_confirmed = False
    st.session_state.lat = -33.8688
    st.session_state.lon = 151.2093
    if "user_persona" not in st.session_state:
        st.session_state.user_persona = "👨‍🚒 Emergency Commander (Gov)"
    
    # --- Fix: Always initialize with the default Technical Agent ---
    st.session_state.assistant = AssistantRouter("ChecklistAssistant")