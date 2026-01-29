import streamlit as st
import modules.auth as auth
import modules.report_generator as report
from src.modules.file_manager import FileManager

# --- Renders the User Management Sidebar ---
def render_sidebar():
    # --- Sidebar for User for Account Settings, Files Management ---
    with st.sidebar:
        st.write(f"👤 **Logged in as:** {st.session_state.username}")
        
        # --- 1. SECURE CHANGE PASSWORD MODULE ---
        with st.expander("🔐 Password Changing"):
            # --- Ask for Current Password ---
            current_password_input = st.text_input("Current Password", type="password", key="curr_pass_input")
            
            # --- Ask for New Password ---
            new_password_input = st.text_input("New Password", type="password", key="new_pass_input")
            confirm_password = st.text_input("Confirm New Password", type="password", key="conf_pass_input")
            
            if st.button("Update Password"):
                # --- Security Step: Verify the OLD password first ---
                if not auth.verify_login(st.session_state.username, current_password_input):
                    st.error("❌ Current password is incorrect. Cannot update.")
                
                # --- Match Validation Step: Check if new passwords match ---
                elif new_password_input != confirm_password:
                    st.error("⚠️ New passwords do not match.")
                
                # --- Rules Validation Step: Check Password Rules ---
                elif not auth.validate_password(new_password_input):
                    st.error("❌ Password must be at least 6 characters long and contain at least one letter.")
                
                # --- Final Step: Execute Change Password ---
                else:
                    if auth.change_password(st.session_state.username, new_password_input):
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error("Error updating password.")

        # --- 2. DANGER ZONE: DELETE ACCOUNT ---
        with st.expander("🚨 Warning: Delete Account in this Tab"):
            st.warning("This action is permanent. All chat history will be lost.")
            
            # --- Step 1: Explicit Checkbox Confirmation ---
            confirm_delete = st.checkbox("Are you sure you want to delete your account?")
            
            # --- Step 2: Only show password field if they checked the box ---
            if confirm_delete:
                del_pass_input = st.text_input("Confirm Password to Delete", type="password", key="del_pass_input")
                
                if st.button("DELETE ACCOUNT PERMANENTLY", type="primary"):
                    if auth.verify_login(st.session_state.username, del_pass_input):
                        # --- Execute Deletion ---
                        auth.delete_user(st.session_state.username)
                        
                        st.success("Account deleted.")
                        
                        # --- Log out and Clear State ---
                        st.session_state.logged_in = False
                        st.session_state.username = ""
                        for key in ["messages", "assistant", "location_confirmed", "copied", "lat", "lon"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password. Deletion cancelled.")

        st.markdown("---")

        # --- 3. FILE User's Documents Managements ---
        st.markdown("### 📂 Upload files/Generate PDF Report")
        # --- 3.1 FILE UPLOAD SECTION: Supported: PDF, DOCX, CSV ---
        uploaded_file = st.file_uploader(
            "Attach a file (PDF, DOCX, CSV)", 
            type=['pdf', 'docx', 'csv', 'txt'],
            label_visibility="collapsed"
        )
        
        
        if uploaded_file: # --- If a file is uploaded, process it and save to session_state ---
            # --- Avoid re-processing if it's the same file we already have ---
            if st.session_state.get('last_uploaded_filename') != uploaded_file.name:
                with st.spinner("Processing file..."):
                    file_text = FileManager.process_file(uploaded_file)
                    st.session_state['pending_file_context'] = file_text
                    st.session_state['last_uploaded_filename'] = uploaded_file.name
                st.success(f"Attached: {uploaded_file.name}")
            else:
                # --- Provide visual feedback that file is ready ---
                st.info(f"Ready: {uploaded_file.name}")
        else:
            # --- Clear context if user removes the file ---
            st.session_state['pending_file_context'] = None
            st.session_state['last_uploaded_filename'] = None
    
        # --- 3.2 REPORT GENERATION: ONLY SHOW IF MESSAGES EXIST ---
        if "messages" in st.session_state and len(st.session_state.messages) > 0:
            if st.button("Generate PDF Report"):
                try:
                    # --- Generate PDF bytes ---
                    pdf_bytes = report.generate_pdf_report(
                        st.session_state.username, 
                        st.session_state.messages
                    )

                    # --- Create the download button ---
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"Wildfire_Report_{st.session_state.username}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Could not generate report: {e}")
        else:
            st.info("Start a conversation to generate a report.")

        st.markdown("---")

        # --- 4. LOGOUT BUTTON: BACK TO LOGIN PAGE ---
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            # --- Clear session state so next user starts fresh ---
            for key in ["messages", "assistant", "location_confirmed", "copied", "lat", "lon"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()