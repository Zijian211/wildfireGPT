import streamlit as st
import modules.auth as auth
import pandas as pd

def render_admin_dashboard():
    """
    Renders the Admin Dashboard for user management.
    """
    st.title("🛡️ Admin Dashboard")
    st.write(f"Welcome back, **{st.session_state.username}**!")
    st.markdown("---")

    st.subheader("👥 User Management System")
    
    # --- 1. Fetch All Users ---
    all_users = auth.get_all_users()
    
    if not all_users:
        st.info("No users found in the database.")
    else:
        # --- Convert to DataFrame for a nice table view ---
        # --- In production, never display raw hashed passwords. ---
        # --- But per users' request, we are showing the stored data. ---
        user_list = [{"Username": user, "Hashed Password": pwd} for user, pwd in all_users.items()]
        df = pd.DataFrame(user_list)
        
        st.dataframe(df, use_container_width=True)
        
        st.markdown("### ❌ Delete a User")
        
        # --- 2. Select User to Delete ---
        user_to_delete = st.selectbox("Select user to remove:", list(all_users.keys()))
        
        if st.button(f"Delete User: {user_to_delete}", type="primary"):
            # --- Prevent Admin from deleting themselves ---
            if user_to_delete == "BenHua":
                st.error("⚠️ You cannot delete the Super Admin account!")
            else:
                auth.delete_user(user_to_delete)
                st.success(f"User '{user_to_delete}' has been permanently deleted.")
                st.rerun()

    st.markdown("---")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()