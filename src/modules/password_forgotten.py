import streamlit as st
import modules.auth as auth
import time

def render_forgot_password_page():
    """Renders the step-by-step password recovery wizard."""
    
    # --- Initialize local state for the wizard ---
    if 'fp_step' not in st.session_state:
        st.session_state.fp_step = 'identifying' # --- identifying -> verifying -> resetting ---
    if 'fp_username' not in st.session_state:
        st.session_state.fp_username = ""

    st.markdown("### 🔐 Password Recovery")
    
    if st.button("← Back to Login"):
        st.session_state.auth_mode = 'login'
        # --- Reset wizard state ---
        st.session_state.fp_step = 'identifying'
        st.rerun()

    # --- STEP 1: IDENTIFY USER ---
    if st.session_state.fp_step == 'identifying':
        st.info("Enter your username to find your account.")
        username_input = st.text_input("Username", key="fp_user_input")
        
        if st.button("Next"):
            questions = auth.get_security_questions(username_input)
            if questions:
                st.session_state.fp_username = username_input
                st.session_state.fp_questions = questions
                st.session_state.fp_step = 'verifying'
                st.rerun()
            else:
                st.error("User not found or no security questions set for this account.")

    # --- STEP 2: VERIFY ANSWERS ---
    elif st.session_state.fp_step == 'verifying':
        st.markdown(f"**Security Check for: `{st.session_state.fp_username}`**")
        st.write("Please answer the following security questions:")
        
        ans1 = st.text_input(f"Q1: {st.session_state.fp_questions[0]}", key="fp_a1")
        ans2 = st.text_input(f"Q2: {st.session_state.fp_questions[1]}", key="fp_a2")
        ans3 = st.text_input(f"Q3: {st.session_state.fp_questions[2]}", key="fp_a3")
        
        if st.button("Verify Answers"):
            if auth.verify_security_answers(st.session_state.fp_username, [ans1, ans2, ans3]):
                st.success("Identity Verified!")
                time.sleep(1)
                st.session_state.fp_step = 'resetting'
                st.rerun()
            else:
                st.error("❌ Incorrect answers. Please try again.")

    # --- STEP 3: RESET PASSWORD ---
    elif st.session_state.fp_step == 'resetting':
        st.success("Identity Confirmed! You can now set a new password.")
        
        new_pw = st.text_input("New Password", type="password", key="fp_new_pw")
        confirm_pw = st.text_input("Confirm Password", type="password", key="fp_conf_pw")
        
        if st.button("Reset Password"):
            if new_pw != confirm_pw:
                st.error("Passwords do not match.")
            elif not auth.validate_password(new_pw):
                st.error("Password must be > 6 chars and contain a letter.")
            else:
                auth.reset_password(st.session_state.fp_username, new_pw)
                st.success("✅ Password successfully reset!")
                time.sleep(2)
                
                # --- Cleanup and Redirect ---
                st.session_state.auth_mode = 'login'
                st.session_state.fp_step = 'identifying'
                st.rerun()