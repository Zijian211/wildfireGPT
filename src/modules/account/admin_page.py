import streamlit as st

# --- Import the separate tab modules ---
from src.modules.account.admin.user_management import render_user_management_tab
from src.modules.account.admin.chat_inspector import render_chat_inspector_tab
from src.modules.account.admin.system_evaluation import render_system_evaluation_tab
from src.modules.account.admin.AI_personaTesting import render_ai_persona_testing_tab

# ==========================================
# --- ADMIN DASHBOARD UI ---
# ==========================================
def render_admin_dashboard():
    st.title("Admin Dashboard 🛠️")
    
    # --- Chat Inspector ---
    tab1, tab2, tab3, tab4 = st.tabs(["User Management", "Chat Inspector", "System Evaluation", "AI Persona Testing"])

    # =================================
    # --- TAB 1: USER MANAGEMENT ---
    # =================================
    with tab1:
        render_user_management_tab()

    # =================================
    # --- TAB 2: CHAT INSPECTOR ---
    # =================================
    with tab2:
        render_chat_inspector_tab()

    # =================================
    # --- TAB 3: SYSTEM EVALUATION ---
    # =================================
    with tab3:
        render_system_evaluation_tab()

    # =================================
    # --- TAB 4: AI PERSONA TESTING ---
    # =================================
    with tab4:
        render_ai_persona_testing_tab()

    st.markdown("---")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()