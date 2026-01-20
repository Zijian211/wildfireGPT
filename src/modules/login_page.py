import streamlit as st
import modules.auth as auth

def render_login_page():
    """
    Renders the Login and Register tabs.
    Handles user authentication and new account creation.
    """
    st.markdown("### Please log in to access your workspace")
    
    tab1, tab2 = st.tabs(["Login", "Register"])

    # --- TAB 1: LOGIN ---
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            if auth.verify_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Incorrect username or password")

    # --- TAB 2: REGISTER ---
    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        
        if st.button("Create Account"):
            # --- 1. Validate Username Format ---
            if not auth.validate_username(new_user):
                st.error("❌ Username can only contain letters and numbers (no special characters).")
            
            # --- 2. Validate Password Strength ---
            elif not auth.validate_password(new_pass):
                st.error("❌ Password must be at least 6 characters long and contain at least one letter.")
            
            # --- 3. Save User ---
            else:
                if auth.save_user(new_user, new_pass):
                    st.success("✅ Account created! Please log in.")
                else:
                    st.error("Username already exists.")