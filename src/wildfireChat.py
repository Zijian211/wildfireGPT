import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Local Imports ---
from src.assistants.assistant_router import AssistantRouter
import streamlit as st
import json
from src.assistants.analyst.utils import display_maps, display_plots
import folium
from streamlit_folium import st_folium
import pickle
from src.utils import stream_static_text
from src.modules import auth as auth, sidebar as sidebar, login_page as login, admin_page as admin
from src.modules.input_box import InputBox

# --- APP TITLE ---
st.title("Wildfire GPT")

# --- AUTH STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- 1. DEFINE THE DOCTOR FIRST ---
def debug_doctor(e):
    """
    Catches ALL errors (Logic & API) and displays them nicely.
    """
    error_msg = str(e)
    # We use a container to ensure it renders on top of everything
    with st.container():
        st.error("🚨 An error stopped the app.")
        with st.expander("🚑 Debug Doctor (Diagnosis)", expanded=True):
            st.code(error_msg, language="python")
            st.markdown("### Diagnosis:")
            
            if "AttributeError" in error_msg and "location_confirmed" in error_msg:
                st.warning("🛠️ **State Memory Error**")
                st.info("The app forgot your location status. The 'Safety Net' below should fix this on reload.")
                if st.button("Fix & Reload"):
                    st.session_state.location_confirmed = False
                    st.session_state.lat = 34.0522
                    st.session_state.lon = -118.2437
                    st.rerun()

            elif "429" in error_msg or "RateLimit" in error_msg:
                st.warning("📉 **API Rate Limit**")
                st.info("You have hit the OpenAI/Groq daily limit.")

            elif "recognition connection" in error_msg:
                st.info("🎤 **Voice API Error**")
                st.info("Google Speech could not connect. Check internet.")
            
            else:
                st.info("🔌 **General System Error**")
                st.markdown("This is an unexpected crash.")

def display_feedback(message, index, file):
    increment = 0
    if message["role"] == "assistant":
        for feedback in ["Correctness", "Relevance", "Entailment", "Accessibility"]:
            feedback_key = f"{feedback}_{index}"
            if feedback_key not in st.session_state:
                st.session_state[feedback_key] = ""

        st.code(message["content"], language=None)

        feedback_dict = {}
        with st.expander("Click to provide feedback"):
            for feedback in ["Correctness", "Relevance", "Entailment", "Accessibility"]:
                if feedback == "Relevance":
                    with st.form(f"Relevance Feedback {index}"):
                        st.write("Relevance Feedback")
                        q1 = st.radio("Does my response answer your last question?", ["Yes", "No", "Could be better", "Not Applicable"])
                        submitted = st.form_submit_button("Submit")
                        if submitted:
                            message["relevance_feedback_q1"] = q1

                if feedback == "Entailment":
                    with st.form(f"Entailment Feedback {index}"):
                        st.write("Entailment Feedback")
                        q1 = st.radio("Do my analyses follow from the data?", ["Yes", "No", "Could be better", "Not Applicable"])
                        submitted = st.form_submit_button("Submit")
                        if submitted:
                            message["entailment_feedback_q1"] = q1

                if feedback == "Accessibility":
                    with st.form(f"Accessibility Feedback {index}"):
                        st.write("Accessibility Feedback")
                        q1 = st.radio("Is there too much jargon?", ["Yes", "No", "Could be better", "Not Applicable"])
                        submitted = st.form_submit_button("Submit")
                        if submitted:
                            message["accessibility_feedback_q1"] = q1
                
                feedback_key = f"{feedback}_{index}"
                feedback_dict[feedback] = st.text_input(f"{feedback} Feedback", key=feedback_key)
                if feedback_dict[feedback]:
                    message[feedback.lower() + "_feedback"] = feedback_dict[feedback]

        increment = 1

    message_save = {k: v for k, v in message.items() if k != "content"}
    message_save["content"] = message["content"] if type(message["content"]) == str else message["content"][0]
    file.write(json.dumps(message_save) + "\n")
    file.flush()
    return increment

def display_reponse(message, index=0, file=None):
    with st.chat_message(message["role"]):
        response = message["content"]
        if type(response) != str:
            response, visualizations = response
            for visualization in visualizations:
                maps, figs = visualization
                if type(maps) == list:
                    display_maps(maps)
                display_plots(figs)
        st.markdown(response)
        return display_feedback(message, index, file)


# --- 2. GLOBAL SAFETY WRAPPER ---
# --- This ensures THE DOCTOR CATCHES EVERYTHING (even logic crashes) ---
try:

    # --- LOGIN / REGISTER LOGIC ---
    if not st.session_state.logged_in:
        login.render_login_page()

    # --- Login for Administrator ---
    elif auth.is_admin(st.session_state.username):
        admin.render_admin_dashboard()

    # --- Login for Regular User Flow ---
    else:    
        sidebar.render_sidebar()

        user_pkl_path = f"chat_history/{st.session_state.username}_session_state.pkl"
        user_jsonl_path = f"chat_history/{st.session_state.username}_interaction.jsonl"

        # --- Save User Profile ---
        user_profile_path = f"chat_history/{st.session_state.username}_profile.txt"
        if not os.path.exists(user_profile_path):
            with open(user_profile_path, "w") as f:
                f.write("Profession: Emergency Manager\nConcern: Fire Safety\nLocation: CA\nTime: Now\nScope: Local")

        # --- STATE INITIALIZATION & RESTORE ---
        if "messages" not in st.session_state:
            try:
                with open(user_pkl_path, "rb") as file:
                    data = pickle.load(file)
                    for key in ["messages", "assistant", "location_confirmed", "copied", "lat", "lon"]:
                        if key in data.keys():
                            st.session_state[key] = data[key]
            except:
                st.session_state.messages = []
                st.session_state.assistant = AssistantRouter("ChecklistAssistant")
                # --- Initial Assistant Message ---
                with st.chat_message("assistant"):
                    full_response = st.session_state.assistant.get_assistant_response()
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.location_confirmed = True
                st.session_state.copied = []
                st.session_state.lat = 34.0522 
                st.session_state.lon = -118.2437

            st.rerun()
        
        elif "messages" in st.session_state:
            try:
                with open(user_pkl_path, "wb") as file:
                    states = {}
                    for key in ["messages", "assistant", "location_confirmed", "copied", "lat", "lon"]:
                        if key in st.session_state.keys():
                            states[key] = st.session_state[key]
                    pickle.dump(states, file)
            except:
                pass

        # --- STATE SAFETY NET ---
        if "location_confirmed" not in st.session_state:
            st.session_state.location_confirmed = False
        if "lat" not in st.session_state:
            st.session_state.lat = 34.0522
        if "lon" not in st.session_state:
            st.session_state.lon = -118.2437
        # ---------------------------------------

        index = 0
        with open(user_jsonl_path, "w") as file:
            for message in st.session_state.messages:
                index += display_reponse(message, index, file)

        # --- LOCATION CONFIRMATION MAP ---
        if st.session_state.location_confirmed == False:
            lat = st.session_state.lat
            lon = st.session_state.lon

            st.write("The map below shows the initial location with 36km radius.")
            m = folium.Map(location=[lat, lon], zoom_start=9)
            folium.Circle(
                location=[lat, lon],
                radius=36000,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.2
            ).add_to(m)

            folium.Marker(location=[lat, lon], popup='Initial Location').add_to(m)
            m.add_child(folium.ClickForMarker(popup='Clicked Location'))
            m.add_child(folium.LatLngPopup())
            map = st_folium(m, height=350, width=700)

            try:
                data = (map['last_clicked']['lat'],map['last_clicked']['lng'])
                m2 = folium.Map(location=[data[0], data[1]], zoom_start=9)
                folium.Marker(location=[lat, lon], popup='Initial Location').add_to(m2)
                folium.Circle(
                    location=data,
                    radius=36000,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.2
                ).add_to(m2)
                stream_static_text(f"Clicked Coordinates:{data}. Please confirm.")
                folium.Marker(location=[data[0], data[1]], popup='New Location').add_to(m2)
                st_folium(m2, height=350, width=700)
            except:
                data = [lat, lon]
                
            if st.button("Confirm Location"):
                st.session_state.location_confirmed = True
                user_prompt = f"The location has been confirmed: latitude {data[0]}, longitude {data[1]}."
                
                with st.chat_message("user"):
                    st.markdown(user_prompt)
                st.session_state.messages.append({"role": "user", "content": user_prompt})
                
                with st.chat_message("assistant"):
                    full_response = st.session_state.assistant.get_assistant_response(user_prompt)
                        
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()

        # --- INPUT SECTION ---
        else:
            user_prompt = InputBox.render()
    
            if user_prompt:
                if user_prompt.lower() == 'resume conversation':
                    st.session_state.assistant.resume_conversation()
                    user_prompt = None
                    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]['role'] == 'assistant':
                        st.session_state.messages.pop(-1)
                    st.rerun()
                else:
                    final_prompt_to_model = user_prompt
                    if st.session_state.get('pending_file_context'):
                        final_prompt_to_model = f"{st.session_state['pending_file_context']}\n\nUser Question: {user_prompt}"

                    with st.chat_message("user"):
                        st.markdown(user_prompt)
                        if st.session_state.get('pending_file_context'):
                             st.caption(f"📎 Context attached: {st.session_state.get('last_uploaded_filename', 'File')}")

                    st.session_state.messages.append({"role": "user", "content": final_prompt_to_model})

                    with st.chat_message("assistant"):
                        full_response = st.session_state.assistant.get_assistant_response(final_prompt_to_model)
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.rerun()

# --- 3. CATCH-ALL EXCEPTION HANDLER ---
except Exception as e:
    debug_doctor(e)
    st.stop()