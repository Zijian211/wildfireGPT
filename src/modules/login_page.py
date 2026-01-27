import streamlit as st
import modules.auth as auth
import modules.register_page as register_page
import modules.password_forgotten as password_forgotten

def render_login_page():
    """
    Main Entry point for Authentication.
    Routes to Login, Register, or Forgot Password pages.
    """
    
    # --- Initialize Navigation State ---
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login' # --- Options: 'login', 'register', 'forgot_password' ---

    # --- ROUTING ---
    if st.session_state.auth_mode == 'register':
        register_page.render_register_page()
        
    elif st.session_state.auth_mode == 'forgot_password':
        password_forgotten.render_forgot_password_page()
        
    else:
        # --- DEFAULT: LOGIN FORM ---
        st.markdown("### Please log in to access your workspace")
        
        # --- We use a container to keep it neat ---
        with st.container():
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Log In", type="primary", use_container_width=True):
                    if auth.verify_login(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Incorrect username or password")
            
            with col2:
                 if st.button("Forgot Password?", type="secondary", use_container_width=True):
                    st.session_state.auth_mode = 'forgot_password'
                    st.rerun()

        st.markdown("---")
        st.markdown("Don't have an account?")
        if st.button("Create New Account"):
            st.session_state.auth_mode = 'register'
            st.rerun()