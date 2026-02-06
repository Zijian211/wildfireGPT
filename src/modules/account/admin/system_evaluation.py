import streamlit as st
import pandas as pd
import os
import shutil
import json
import time
import gc
import pickle
import glob
from src.evaluation.eval_offline import Evaluator
from src.modules.database.profile_manager import extract_profession_from_persona

# ==========================================
# --- THE DEBUG DOCTOR (File System Fixer) ---
# ==========================================
def diagnose_and_clean(folder_path):
    """
    Attempts to clean a folder safely. 
    """
    gc.collect() 
    
    # --- Ensure folder exists ---
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return True, "Created new folder."

    # --- Files to clean up before new run ---
    files_to_remove = ["interaction.jsonl", "tools.txt", "user_profile.txt", "evaluation.csv", "data_dict.json"]
    
    for filename in files_to_remove:
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            success = False
            for attempt in range(3):
                try:
                    os.remove(file_path)
                    success = True
                    break
                except PermissionError:
                    time.sleep(0.5) 
                except Exception as e:
                    return False, f"Error deleting {filename}: {str(e)}"
            
            if not success:
                return False, f"LOCKED FILE: {filename} is currently in use. Please restart the app."

    return True, "Cleaned successfully."

def render_system_evaluation_tab():
    st.subheader("Evaluation for AI Conversation Quality of WildfireGPT")
    st.info("This tool runs the evaluation script on a specific user's interaction history.")

    # --- 1. Select User Case ---
    case_root = os.path.abspath("cases") # --- Force Absolute Path ---
    if not os.path.exists(case_root):
        os.makedirs(case_root)
        
    available_users = [f.replace("_interaction.jsonl", "") for f in os.listdir("chat_history") if f.endswith("_interaction.jsonl")]
    
    if not available_users:
        st.warning("No chat history found.")
    else:
        selected_user = st.selectbox("Select User Session to Evaluate", available_users)
        
        if st.button("1. Prepare Data & Run Evaluation"):
            # --- Use absolute path to prevent folder confusion ---
            case_folder = os.path.join(case_root, f"{selected_user}_live_session")
            
            # --- A. CLEANUP ---
            status, msg = diagnose_and_clean(case_folder)
            if not status:
                st.error(f"⚠️ {msg}")
                st.stop()
            
            # --- B. GENERATE EVALUATION DATA (From Pickle) ---
            session_file = os.path.join("chat_history", f"{selected_user}_session_state.pkl")
            dst_interaction = os.path.join(case_folder, "interaction.jsonl")

            if os.path.exists(session_file) and os.path.getsize(session_file) > 0:
                try:
                    with open(session_file, "rb") as f:
                        saved_state = pickle.load(f)
    
                    # --- 1. Extract Messages ---
                    messages = saved_state.get("messages", [])
                    if not messages:
                        st.error("⚠️ Chat history is empty in the session file.")
                        st.stop()
    
                    # --- 2. Write to interaction.jsonl ---
                    with open(dst_interaction, "w", encoding="utf-8") as outfile:
                        for msg in messages:
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "")
            
                            if isinstance(content, tuple):
                                content = content[0]
            
                            entry = {
                                "role": role, 
                                "content": str(content)
                            }
                            outfile.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
                    # --- 3. Extract Context Files ---
                    tools_path = os.path.join("chat_history", "tools.txt")
                    if os.path.exists(tools_path):
                        with open(tools_path, "r", encoding="utf-8") as tf:
                            tools_content = tf.read()
                    else:
                        tools_content = "Tools: No tools data available."
    
                    with open(os.path.join(case_folder, "tools.txt"), "w", encoding="utf-8") as t:
                        t.write(tools_content)
    
                    # --- USER PROFILE EXTRACTION ---
                    json_profile_path = os.path.join("chat_history", f"{selected_user}_eval_profile.json")
                    text_profile_path = os.path.join("chat_history", f"{selected_user}_profile.txt")
                    old_profile_path = os.path.join("chat_history", "user_profile.txt")
    
                    user_profile_content = ""
    
                    if os.path.exists(json_profile_path):
                        try:
                            with open(json_profile_path, "r", encoding="utf-8") as jf:
                                profile_data = json.load(jf)
                            # Use persona_clean if available, otherwise persona
                            persona = profile_data.get('persona_clean', profile_data.get('persona', 'Unknown'))
                            user_profile_content = f"""User: {profile_data.get('username', selected_user)}
Persona: {persona}
Profession: {profile_data.get('profession', 'Unknown')}
Location: Latitude {profile_data.get('location', {}).get('lat', 'Unknown')}, Longitude {profile_data.get('location', {}).get('lon', 'Unknown')}
Concern: {profile_data.get('concern', 'Wildfire risk assessment')}
Timeline: {profile_data.get('timeline', 'Current assessment')}
Created: {profile_data.get('created_at', 'Unknown')}"""
                        except Exception as e:
                            st.warning(f"Could not read JSON profile: {e}")
                    elif os.path.exists(text_profile_path):
                        with open(text_profile_path, "r", encoding="utf-8") as pf:
                            user_profile_content = pf.read()
                    elif os.path.exists(old_profile_path):
                        with open(old_profile_path, "r", encoding="utf-8") as pf:
                            user_profile_content = pf.read()
                    else:
                        persona = saved_state.get("user_persona", "👨‍🚒 Emergency Commander (Gov)")
                        lat = saved_state.get("lat", "Unknown")
                        lon = saved_state.get("lon", "Unknown")

                        # --- Remove emojis from persona for text file ---
                        import re
                        persona_clean = re.sub(r'[^\w\s\-\(\)]', '', persona).strip()

                        # --- Analyze conversation for actual personas used ---
                        conversation_personas = []
                        for msg in messages:
                            if msg.get("role") == "assistant":
                                content = msg.get("content", "")
                                if isinstance(content, tuple):
                                    content = content[0]
                                
                                # --- Check for persona mentions ---
                                if 'School Principal' in content:
                                    conversation_personas.append('School Principal')
                                elif 'Logistics Manager' in content:
                                    conversation_personas.append('Logistics Manager')
                                elif 'Insurance Risk Assessor' in content:
                                    conversation_personas.append('Insurance Risk Assessor')
                                elif 'Power Grid Operator' in content:
                                    conversation_personas.append('Power Grid Operator')
                                elif 'Real Estate Developer' in content:
                                    conversation_personas.append('Real Estate Developer')
                                elif 'Park Ranger' in content or 'Tourism' in content:
                                    conversation_personas.append('Park Ranger / Tourism')
                                elif 'Other Careers' in content:
                                    conversation_personas.append('Other Professional')
                                elif 'Emergency Commander' in content:
                                    conversation_personas.append('Emergency Commander (Gov)')

                        # --- Deduplicate while preserving order ---
                        seen = set()
                        unique_personas = []
                        for p in conversation_personas:
                            if p not in seen:
                                seen.add(p)
                                unique_personas.append(p)

                        # --- Determine profession based on conversation flow ---
                        if len(unique_personas) > 0:
                            # --- Use the most common persona or the last one ---
                            from collections import Counter
                            persona_counter = Counter(conversation_personas)
                            most_common_persona = persona_counter.most_common(1)[0][0] if persona_counter else unique_personas[-1]
                            profession = most_common_persona
                        else:
                            profession = extract_profession_from_persona(persona)

                        concern = "Wildfire risk assessment"
                        for msg in messages:
                            if msg.get("role") == "user" and len(msg.get("content", "")) > 10:
                                content = msg.get("content", "")
                                if isinstance(content, tuple):
                                    content = content[0]
                                concern = content[:100] + "..." if len(content) > 100 else content
                                break
                        
                        user_profile_content = f"""User: {selected_user}
Persona: {persona_clean}
Profession: {profession}
Location: Latitude {lat}, Longitude {lon}
Concern: {concern}
Timeline: Current assessment
Actual Personas in Conversation: {', '.join(unique_personas) if unique_personas else 'None detected'}
Status: Live consultation session
Notes: Profile generated from session data with persona analysis"""

                    with open(os.path.join(case_folder, "user_profile.txt"), "w", encoding="utf-8") as p:
                        p.write(user_profile_content)

                except Exception as e:
                    st.error(f"Failed to generate evaluation data from session: {e}")
                    st.write(f"Error details: {str(e)}")
                    st.stop()
            else:
                st.error(f"❌ Session file not found or is empty: {session_file}")
                st.stop()

            # --- C. RUN EVALUATION ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                args = {
                    'llm_model': 'gpt-4-turbo', 
                    'case_folder': case_folder, # --- Passing absolute path ---
                    'verbose': False
                }
                
                status_text.text("Initializing Evaluator...")
                evaluator = Evaluator(args)
                
                status_text.text("Running LLM Evaluation (this may take a minute)...")
                evaluator.llm_evaluate()
                
                # --- Give file system a moment to write the CSV ---
                time.sleep(2)
                
                progress_bar.progress(100)
                status_text.success("Evaluation Complete!")
                
                # --- D. DISPLAY RESULTS ---
                csv_path = os.path.join(case_folder, "evaluation.csv")
                
                if os.path.exists(csv_path):
                    eval_df = pd.read_csv(csv_path)
                    st.divider()
                    st.markdown("### 📊 Evaluation Results")
                    
                    if eval_df.empty:
                        st.warning("Evaluation ran, but the CSV is empty.")
                    else:
                        # --- Metrics ---
                        col1, col2 = st.columns(2)
                        total_checks = len(eval_df)
                        passed_checks = len(eval_df[eval_df['input_score'].astype(str).str.contains("Yes", na=False)])
                        
                        col1.metric("Total Interactions Checked", total_checks)
                        pass_rate = int((passed_checks/total_checks)*100) if total_checks > 0 else 0
                        col2.metric("Pass Rate", f"{pass_rate}%")
                        
                        st.subheader("Detailed Report")
                        st.dataframe(eval_df[['aspect', 'input_score', 'reasoning']], use_container_width=True)
                else:
                    # --- DEBUG INFO IF FAILS ---
                    st.error("Evaluation script ran, but 'evaluation.csv' was not found.")
                    st.write(f"📂 Checked folder: `{case_folder}`")
                    st.write("📂 Files actually found there:", os.listdir(case_folder))
                    
            except Exception as e:
                st.error(f"Evaluation Process Failed: {str(e)}")
                st.write(e)