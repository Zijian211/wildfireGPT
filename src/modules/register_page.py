import streamlit as st
import modules.auth as auth

def render_register_page():
    """
    Renders the Registration Page.
    Includes Password Confirmation and Security Questions.
    """
    st.markdown("### 📝 Create New Account")
    
    # Back Button
    if st.button("← Back to Login"):
        st.session_state.auth_mode = 'login'
        st.rerun()
    
    st.write("Please fill in the details below to register.")

    # --- 1. Credentials ---
    with st.container():
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        # ADDED: Password Confirmation
        confirm_pass = st.text_input("Confirm Password", type="password", key="reg_pass_confirm")
    
    st.markdown("---")
    
    # --- 2. Security Questions ---
    st.write("**🔐 Security Questions**")
    st.caption("Select 3 different questions. These will be used to recover your account.")
    
    q_lib = auth.SECURITY_QUESTIONS_LIBRARY
    
    # Question 1
    q1 = st.selectbox("Question 1", q_lib, index=0)
    a1 = st.text_input("Answer 1", type="password", help="Answers are case-insensitive.")
    
    # Question 2 (Exclude selected)
    q2_opts = [q for q in q_lib if q != q1]
    q2 = st.selectbox("Question 2", q2_opts, index=0 if len(q2_opts)>0 else 0)
    a2 = st.text_input("Answer 2", type="password")
    
    # Question 3
    q3_opts = [q for q in q_lib if q not in [q1, q2]]
    q3 = st.selectbox("Question 3", q3_opts, index=0 if len(q3_opts)>0 else 0)
    a3 = st.text_input("Answer 3", type="password")

    st.markdown("---")

    if st.button("Create Account", type="primary"):
        # --- VALIDATION ---
        if not auth.validate_username(new_user):
            st.error("❌ Username can only contain letters and numbers.")
        
        elif not auth.validate_password(new_pass):
            st.error("❌ Password must be > 6 chars and contain a letter.")
        
        elif new_pass != confirm_pass:
            st.error("❌ Passwords do not match.")
            
        elif not (a1 and a2 and a3):
            st.error("❌ Please answer all 3 security questions.")
            
        elif len({q1, q2, q3}) < 3:
                st.error("❌ Please choose 3 different questions.")
        
        else:
            # --- SAVE USER ---
            sec_data = [
                {'question': q1, 'answer': a1},
                {'question': q2, 'answer': a2},
                {'question': q3, 'answer': a3}
            ]
            
            if auth.save_user(new_user, new_pass, sec_data):
                st.success("✅ Account created successfully!")
                st.balloons()
                # Redirect to login
                st.session_state.auth_mode = 'login'
                st.rerun()
            else:
                st.error("❌ User already exists. Please choose a different username.")