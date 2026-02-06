import streamlit as st
import modules.account.auth as auth

def render_user_management_tab():
    """
    User Management Tab for Admins to view and manage registered users.
    """
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