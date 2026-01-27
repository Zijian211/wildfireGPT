import streamlit as st
import modules.auth as auth
import pandas as pd
import os
import shutil
import json
import time
import gc
from src.evaluation.eval_offline import Evaluator

# ==========================================
# 🚑 THE DEBUG DOCTOR (File System Fixer)
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

# ==========================================
# --- ADMIN DASHBOARD UI ---
# ==========================================
def render_admin_dashboard():
    st.title("Admin Dashboard 🛠️")
    
    tab1, tab2 = st.tabs(["User Management", "System Evaluation"])

    # =================================
    # --- TAB 1: USER MANAGEMENT ---
    # =================================
    with tab1:
        st.subheader("Registered Users")
        users = auth.get_all_users()
        
        if not users:
            st.info("No users registered yet.")
        else:
            # --- Display User Details ---
            user_list = []
            for u, data in users.items():
                
                # --- Handle legacy string users with solely password hash ---
                if isinstance(data, str):
                    password_display = data[:15] + "..."
                    sec_info = "None (Legacy Account)"
                else:
                    # --- Modern dict user with hashed password and security questions ---
                    password_display = data.get('password', '')[:15] + "..."
                    sec_info = "None"
                    if "security_questions" in data and data["security_questions"]:
                        sec_details = []
                        for idx, item in enumerate(data["security_questions"]):
                            sec_details.append(f"Q{idx+1}: {item['question']}")
                        sec_info = "\n".join(sec_details)
                
                # --- Append to user list for display ---
                user_list.append({
                    "Username": u, 
                    "Password Hash": password_display,
                    "Security Data": sec_info
                })
            
            # --- Show in expandable sections ---
            for user_row in user_list:
                with st.expander(f"👤 {user_row['Username']}"):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.text("Password Hash:")
                        st.code(user_row['Password Hash'], language="text")
                        
                        # --- Admin is allowed to delete users ---
                        if st.button(f"Delete {user_row['Username']}", key=f"del_{user_row['Username']}"):
                            if auth.delete_user(user_row['Username']):
                                st.success(f"Deleted {user_row['Username']}")
                                st.rerun()
                    with col2:
                        st.text("Security Questions:")
                        st.text(user_row['Security Data'])

    # =================================
    # --- TAB 2: SYSTEM EVALUATION ---
    # =================================
    with tab2:
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
                
                # --- B. COPY FILES ---
                try:
                    src_interaction = os.path.join("chat_history", f"{selected_user}_interaction.jsonl")
                    dst_interaction = os.path.join(case_folder, "interaction.jsonl")
                    
                    # --- CHECK: Verify source exists and is not empty ---
                    if not os.path.exists(src_interaction) or os.path.getsize(src_interaction) == 0:
                        st.error("⚠️ The interaction history file for this user is empty! Cannot evaluate.")
                        st.stop()
                        
                    shutil.copy(src_interaction, dst_interaction)
                    
                    # --- Copy Session State (Pickle) ---
                    session_file = os.path.join("chat_history", f"{selected_user}_session_state.pkl")
                    import pickle
                    if os.path.exists(session_file):
                        with open(session_file, "rb") as f:
                            saved_state = pickle.load(f)
                            with open(os.path.join(case_folder, "tools.txt"), "w", encoding="utf-8") as t:
                                t.write(saved_state.get("tools_content", ""))
                            with open(os.path.join(case_folder, "user_profile.txt"), "w", encoding="utf-8") as p:
                                p.write(saved_state.get("user_profile_content", ""))

                except Exception as e:
                    st.error(f"File Copy Failed: {e}")
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

    st.markdown("---")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()