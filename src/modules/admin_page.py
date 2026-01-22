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
    If it fails, it reports EXACTLY which file is locked.
    """
    # 1. Force Python to release memory/file handles from previous runs
    gc.collect() 
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return True, "Created new folder."

    # 2. Try to clean specific files one by one
    files_to_remove = ["interaction.jsonl", "tools.txt", "user_profile.txt", "evaluation.csv", "data_dict.json"]
    
    for filename in files_to_remove:
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            success = False
            # Retry loop: Try 3 times to delete the file
            for attempt in range(3):
                try:
                    os.remove(file_path)
                    success = True
                    break
                except PermissionError:
                    time.sleep(0.5) # Wait 0.5s and try again
                    gc.collect() # Try to force close handles again
                except Exception as e:
                    return False, f"Unexpected error deleting {filename}: {str(e)}"
            
            if not success:
                return False, f"CRITICAL LOCK: The file '{filename}' is open in another program (likely Excel or a previous Python process). Please close it."

    return True, "Folder cleaned successfully."


# ==========================================
# 🌉 DATA BRIDGE (Chat History -> Evaluator)
# ==========================================
def prepare_data_for_eval(username):
    """
    Transforms raw chat history into the strict format required by eval_offline.py.
    """
    # --- 1. Define paths ---
    # MAKE SURE your files are named exactly like this in the folder!
    source_jsonl = f"chat_history/{username}_interaction.jsonl"
    target_folder = f"cases/{username}_live_session"
    
    if not os.path.exists(source_jsonl):
        # DEBUG TIP: Print what file it was looking for
        print(f"DEBUG: Could not find file: {os.path.abspath(source_jsonl)}")
        return None, f"User '{username}' has no chat history file. (Looked for: {source_jsonl})"

    # --- 2. Run the Debug Doctor ---
    success, message = diagnose_and_clean(target_folder)
    if not success:
        return None, f"Windows File Error: {message}"

    # --- 3. Copy/Sync interaction.jsonl ---
    try:
        shutil.copy(source_jsonl, f"{target_folder}/interaction.jsonl")
    except Exception as e:
        return None, f"Failed to copy chat history: {str(e)}"

    # --- 4. Create User Profile ---
    try:
        with open(f"{target_folder}/user_profile.txt", "w", encoding='utf-8') as f:
            f.write(f"Profession: Emergency Manager\n")
            f.write(f"Concern: wildfire safety\n")
            f.write(f"Location: CA\n")
            f.write(f"Time: current\n")
            f.write(f"Scope: regional\n")
    except Exception as e:
        return None, f"Failed to create profile: {str(e)}"

    # --- 5. Generate tools.txt (With Validation) ---
    try:
        chat_entries = []
        valid_pairs_count = 0  # Counter for valid Q&A pairs

        # Use utf-8-sig to handle Windows BOM if present
        with open(source_jsonl, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if line.strip():
                    try:
                        chat_entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue # Skip bad lines
        
        with open(f"{target_folder}/tools.txt", "w", encoding='utf-8') as f:
            # Loop through messages to find User -> Assistant pairs
            for i in range(len(chat_entries) - 1):
                msg = chat_entries[i]
                next_msg = chat_entries[i+1]

                # Match User Question followed by Assistant Answer
                if msg.get('role') == 'user' and next_msg.get('role') == 'assistant':
                    valid_pairs_count += 1
                    
                    user_text = str(msg.get('content', '')).replace('\n', ' ')
                    
                    # Handle AI content being a list or string
                    ai_content = next_msg.get('content', '')
                    if isinstance(ai_content, list):
                        ai_text = str(ai_content[0]) if ai_content else ""
                    else:
                        ai_text = str(ai_content)
                    
                    ai_text = ai_text.replace('\n', ' ')

                    # Strict Format Writing required by Evaluator
                    f.write("**Tool Outputs**\n")
                    f.write(f"Previous Query: {user_text}\n")
                    f.write("System Note: Live session log.\n")
                    f.write("----------\n") 
                    f.write("**LLM Response**\n")
                    f.write(f"{ai_text}\n\n")
        
        # --- NEW CHECK: Stop if no conversations were found ---
        if valid_pairs_count == 0:
            return None, f"User '{username}' has data, but no complete 'User Question -> AI Answer' pairs found. Please chat with the bot first."

    except Exception as e:
        return None, f"Error building tools.txt: {str(e)}"

    return target_folder, "Success"


# ==========================================
# 🖥️ ADMIN DASHBOARD UI
# ==========================================
def render_admin_dashboard():
    """
    Renders the Admin Dashboard for user management and evaluations.
    """
    st.title("🛡️ Admin Dashboard")
    st.write(f"Welcome back, **{st.session_state.username}**!")
    st.markdown("---")

    # --- 1. USER MANAGEMENT SECTION ---
    st.subheader("👥 User Management System")
    
    all_users = auth.get_all_users()
    
    if not all_users:
        st.info("No users found in the database.")
    else:
        # Secure display
        user_list = [{"Username": user, "Hashed Password": pwd, "Status": "Active"} for user, pwd in all_users.items()]
        df = pd.DataFrame(user_list)
        st.dataframe(df, use_container_width=True)
        
        st.markdown("### ❌ Delete a User")
        user_to_delete = st.selectbox("Select user to remove:", list(all_users.keys()))
        
        if st.button(f"Delete User: {user_to_delete}", type="primary"):
            if user_to_delete == "BenHua":
                st.error("⚠️ You cannot delete the Super Admin account!")
            else:
                auth.delete_user(user_to_delete)
                st.success(f"User '{user_to_delete}' has been permanently deleted.")
                st.rerun()

    st.markdown("---")

    # --- 2. EVALUATION STATISTICS SECTION ---
    st.subheader("📊 AI Evaluation Inspector")
    st.info("Select a user to run the AI Grader on their recent conversation.")
    
    # Select a user to grade
    eval_user = st.selectbox("Select User to Audit:", list(all_users.keys()), key="eval_select")

    if st.button("🚀 Run AI Evaluation"):
        with st.spinner(f"Compiling data and grading {eval_user}'s session..."):
            
            # A. Prepare the data folder
            case_folder, status = prepare_data_for_eval(eval_user)
            
            if not case_folder:
                st.error(status)
            else:
                # B. Configure the Evaluator
                args = {
                    'case_folder': case_folder,
                    'llm_model': 'gpt-4-turbo', 
                    'verbose': False
                }
                
                try:
                    # C. Run the Pipeline
                    evaluator = Evaluator(args)
                    evaluator.llm_evaluate()
                    
                    # D. Display Results
                    csv_path = os.path.join(case_folder, "evaluation.csv")
                    if os.path.exists(csv_path):
                        st.success("Evaluation Complete!")
                        
                        # Load Data
                        eval_df = pd.read_csv(csv_path)
                        
                        if eval_df.empty:
                            st.warning("Report generated but it is empty. Check if the user chat history is sufficient.")
                        else:
                            # 1. Metrics Overview
                            col1, col2 = st.columns(2)
                            total_checks = len(eval_df)
                            
                            # Count positive matches (handling potential NaN)
                            passed_checks = len(eval_df[eval_df['input_score'].astype(str).str.contains("Yes", na=False)])
                            
                            col1.metric("Total Interactions Checked", total_checks)
                            pass_rate = int((passed_checks/total_checks)*100) if total_checks > 0 else 0
                            col2.metric("Pass Rate (AI Graded)", f"{pass_rate}%")
                            
                            # 2. Detailed Table
                            st.subheader("Detailed Report")
                            # Display key columns
                            st.dataframe(eval_df[['aspect', 'input_score', 'reasoning']], use_container_width=True)
                        
                    else:
                        st.error("Evaluation script ran, but no CSV was generated. Data preparation might be incomplete.")
                        
                except Exception as e:
                    st.error(f"Evaluation Process Failed: {str(e)}")
                    st.write("Debug info:", e)

    st.markdown("---")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()