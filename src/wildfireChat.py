import sys
import os

# --- 1. BEFORE IMPORTING LOCAL MODULES ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- 2. Local Imports ---
from src.assistants.assistant_router import AssistantRouter
from src.assistants.analyst.utils import display_maps, display_plots
from src.utils import stream_static_text
from src.modules.account import auth as auth, login_page as login, admin_page as admin
from src.modules.database import session_manager as session_manager
from src.modules.database.profile_manager import save_user_profile_for_evaluation
from src.modules.ui.input_box import InputBox
import src.modules.ui.sidebar as sidebar
from src.modules.ui.context_manager import build_enhanced_prompt

# --- Third Party Imports ---
import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import pickle

# --- APP TITLE ---
st.title("Wildfire GPT")

# --- 1. Login State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- 2. User Persona Initialization ---
if "user_persona" not in st.session_state:
    st.session_state.user_persona = "👨‍🚒 Emergency Commander (Gov)"

# --- 3. Map & Location Defaults ---
if "location_confirmed" not in st.session_state:
    st.session_state.location_confirmed = False

if "lat" not in st.session_state:
    st.session_state.lat = -33.8688  # --- Default Lat ---
if "lon" not in st.session_state:
    st.session_state.lon = 151.2093  # --- Default Lon ---

# --- 4. Chat History & Files ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_file_context" not in st.session_state:
    st.session_state.pending_file_context = None

if "last_uploaded_filename" not in st.session_state:
    st.session_state.last_uploaded_filename = None

# --- 5. AI ASSISTANT ---
if "assistant" not in st.session_state or st.session_state.assistant is None:
    st.session_state.assistant = AssistantRouter("ChecklistAssistant")

# --- FUNCTION TO DISPLAY FEEDBACK FOR ASSISTANT MESSAGES ---
def display_feedback(message, index, file):
    """
    Displays Thumbs Up/Down buttons for assistant messages 
    and logs feedback to the JSONL file.
    """
    # --- Default increment is 1 to keep message indexing moving forward ---
    increment = 1
    
    if message["role"] == "assistant":
        # --- Create small columns for the buttons ---
        col1, col2, col3 = st.columns([0.05, 0.05, 0.9])
        
        with col1:
            if st.button("👍", key=f"thumbs_up_{index}", help="This response was helpful"):
                log_entry = {
                    "index": index,
                    "user": st.session_state.username,
                    "feedback": "positive",
                    "content_snippet": str(message["content"])[:50]
                }
                # --- Write to the open file handle ---
                if file:
                    file.write(json.dumps(log_entry) + "\n")
                st.toast("Feedback saved: Helpful! 👍")

        with col2:
            if st.button("👎", key=f"thumbs_down_{index}", help="This response was not helpful"):
                log_entry = {
                    "index": index,
                    "user": st.session_state.username,
                    "feedback": "negative",
                    "content_snippet": str(message["content"])[:50]
                }
                if file:
                    file.write(json.dumps(log_entry) + "\n")
                st.toast("Feedback saved: Not helpful 👎")
    
    return increment

def display_reponse(message, index=0, file=None):
    with st.chat_message(message["role"]):
        response = message["content"]
        
        # --- Handle Tuple (Text, Visualizations) for Schema Compatibility ---
        if isinstance(response, tuple):
            response_text, visualizations = response
            for visualization in visualizations:
                maps, figs = visualization
                if isinstance(maps, list):
                    display_maps(maps)
                display_plots(figs)
            st.markdown(response_text)
        elif type(response) != str:
            # --- Fallback for old complex types if any ---
            response, visualizations = response
            for visualization in visualizations:
                maps, figs = visualization
                if type(maps) == list:
                    display_maps(maps)
                display_plots(figs)
            st.markdown(response)
        else:
            st.markdown(response)
        
        # --- Calling the feedback function and returning its increment ---
        return display_feedback(message, index, file)

# --- LOGIN / REGISTER LOGIC ---
if not st.session_state.logged_in:
    login.render_login_page()

# --- Login for Administrator ---
elif auth.is_admin(st.session_state.username):
    admin.render_admin_dashboard()

# --- Login for Regular User Flow ---
else:    
    # --- Load Session BEFORE UI Renders ---
    session_manager.load_user_session(st.session_state.username)

    sidebar.render_sidebar()

    # --- Define User-Specific File Paths ---
    user_jsonl_path = f"chat_history/{st.session_state.username}_interaction.jsonl"

    # --- Render Chat History ---
    index = 0
    with open(user_jsonl_path, "a+") as file:
        for message in st.session_state.messages:
            index += display_reponse(message, index, file)

    # =========================================================
    # --- MAP & LOCATION SELECTION (FIRST TIME) ---
    # =========================================================
    if st.session_state.location_confirmed == False:
        lat = st.session_state.lat
        lon = st.session_state.lon

        st.info("📍 Step 1: Please confirm your location on the map below.")
        
        m = folium.Map(location=[lat, lon], zoom_start=9)
        folium.Circle(location=[lat, lon], radius=36000, color='red', fill=True, fill_opacity=0.2).add_to(m)
        folium.Marker(location=[lat, lon], popup='Initial').add_to(m)
        m.add_child(folium.ClickForMarker(popup='Selected'))
        m.add_child(folium.LatLngPopup())
        map_data = st_folium(m, height=350, width=700)

        selected_lat, selected_lon = lat, lon
        if map_data and map_data.get('last_clicked'):
            selected_lat = map_data['last_clicked']['lat']
            selected_lon = map_data['last_clicked']['lng']

        # --- Button to confirm the location ---
        if st.button("Confirm Location"):
            st.session_state.lat = selected_lat
            st.session_state.lon = selected_lon
            st.session_state.location_confirmed = True
            
            # --- Save Session Immediately ---
            session_manager.save_user_session(st.session_state.username)
            
            # --- Save User Profile for Evaluation ---
            save_user_profile_for_evaluation(
                username=st.session_state.username,
                persona=st.session_state.user_persona,
                lat=selected_lat,
                lon=selected_lon,
                concern="Location confirmed for wildfire risk assessment"
            )
            
            # ---  SYSTEM INJECTION: Force Sidebar Selection ---
            system_instruction = (
                f"[SYSTEM] User confirmed location at Lat: {selected_lat}, Lon: {selected_lon}. "
                "Do NOT start the analysis yet. "
                "Politely acknowledge the location, then explicitly instruct the user "
                "to select their 'Role & Context' and 'Operation Mode' in the left Sidebar "
                "before proceeding."
            )
            
            st.session_state.messages.append({"role": "user", "content": f"Location confirmed: {selected_lat}, {selected_lon}"})
            
            with st.spinner("Initializing location context..."):
                full_response = st.session_state.assistant.get_assistant_response(system_instruction)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # --- Save again after the assistant greeting ---
            session_manager.save_user_session(st.session_state.username)
            st.rerun()

    # =========================================================
    # --- MAIN CHAT INTERFACE ---
    # =========================================================
    else:
        # --- 1. GET INPUT ---
        user_prompt = InputBox.render()

        # --- 2. PROCESS INPUT ---
        if user_prompt:
            if user_prompt.lower() == 'resume conversation':
                st.session_state.assistant.resume_conversation()
                if len(st.session_state.messages) > 0: st.session_state.messages.pop(-1)
                st.rerun()
            
            else:
                # --- Context Injection ---
                final_prompt_to_model, badges = build_enhanced_prompt(user_prompt, st.session_state)

                # --- Handle "Other Careers" patching ---
                if "Other Careers" in st.session_state.get("user_persona", ""):
                     if "Other Careers" not in final_prompt_to_model: 
                        final_prompt_to_model += "\n[SYSTEM: User is in 'Other Careers' mode. Adapt to their specific role if mentioned.]"

                # --- UI Rendering ---
                with st.chat_message("user"):
                    st.markdown(user_prompt)
                    if badges: st.caption(" | ".join(badges))

                st.session_state.messages.append({"role": "user", "content": user_prompt})

                with st.chat_message("assistant"):
                    full_response = st.session_state.assistant.get_assistant_response(final_prompt_to_model)

                    # --- Source Transparency Logic ---
                    # --- Check if 'badges' list contains a file icon ---
                    has_file_source = any("📎" in badge for badge in badges)
                    if has_file_source:
                        source_footer = "\n\n---\n*Sources: 📄 Uploaded File | 🧠 General Knowledge*"
                    else:
                        source_footer = "\n\n---\n*Source: 🧠 General Knowledge*"
                    
                    full_response += source_footer
                    st.markdown(full_response)
                
                # --- Append response with footer to history ---
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # --- Save Session After Every Message ---
                session_manager.save_user_session(st.session_state.username)
                
                st.session_state['pending_file_context'] = None 
                st.rerun()