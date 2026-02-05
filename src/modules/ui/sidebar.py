import streamlit as st
import modules.account.auth as auth
import modules.ui.report_generator as report
from src.modules.ui.file_manager import FileManager
from src.modules.database import session_manager as session_manager
from src.modules.database.profile_manager import save_user_profile_for_evaluation
from src.assistants.assistant_router import AssistantRouter
import pandas as pd

def render_sidebar():
    """
    Hybrid Sidebar:
    - TOP: Business Logic (Hidden until Location Confirmed)
    - BOTTOM: Account Utilities (Always Visible)
    """
    with st.sidebar:
        st.title("🔥 Wildfire GPT")
        st.caption(f"👤 User: **{st.session_state.username}**")
        
        # =========================================================
        # --- LOGIC GATE: HIDE CONTROLS UNTIL LOCATION CONFIRMED ---
        # =========================================================
        # We only show the Business Context controls if the user has 
        # finished the "Map Phase" (Step 1).
        if st.session_state.get("location_confirmed", False):
            
            st.divider()
            
            # =========================================================
            # --- PART 1: BUSINESS CONTEXT (Role & Mode)
            # =========================================================
            st.subheader("1. Role & Context")
            
            # --- 1.1 Persona Selector ---
            current_persona = st.session_state.get("user_persona", "👨‍🚒 Emergency Commander (Gov)")
            
            # Track previous persona to detect changes
            if "previous_persona" not in st.session_state:
                st.session_state.previous_persona = current_persona

            # --- SMART LOGIC: Define Options & Find Index ---
            persona_options = [
                "👨‍🚒 Emergency Commander (Gov)",
                "🛡️ Insurance Risk Assessor",
                "⚡ Power Grid Operator",
                "🚚 Logistics Manager",
                "🏗️ Real Estate Developer",
                "🏞️ Park Ranger / Tourism",
                "🎓 Other Careers (Student/Researcher...)"
            ]

            # Calculate Index safely based on loaded data
            try:
                default_index = persona_options.index(current_persona)
            except ValueError:
                default_index = 0 

            persona = st.selectbox(
                "Select User Persona:",
                persona_options,
                index=default_index, 
                key="persona_selector",
                help="Select the commercial profile to adjust AI reasoning."
            )
            
            # Update State & Save Immediately if Changed
            if persona != st.session_state.user_persona:
                st.session_state.user_persona = persona
                session_manager.save_user_session(st.session_state.username)
                st.rerun()

            # --- 1.2 Operation Mode ---
            st.subheader("2. Operation Mode")
            
            app_mode = st.radio(
                "Select Module:",
                ["📊 Dashboard (Map View)", "✅ Checklist (SOP)", "♟️ Strategic Plan", "📈 Data Analysis"],
                index=1
            )

            # =========================================================
            # --- SMART SWITCHING LOGIC (Reactive & History Preserving)
            # =========================================================
            
            # Mapping Modes to Technical Agents
            target_agent = "ChecklistAssistant"
            if "Strategic Plan" in app_mode: target_agent = "PlanAssistant"
            elif "Data Analysis" in app_mode: target_agent = "AnalystAssistant"
            elif "Checklist" in app_mode: target_agent = "ChecklistAssistant"
            elif "Dashboard" in app_mode: target_agent = "ChecklistAssistant"

            if "last_app_mode" not in st.session_state:
                st.session_state.last_app_mode = app_mode

            # Check for changes in Mode OR Persona
            mode_changed = st.session_state.last_app_mode != app_mode
            persona_changed = st.session_state.previous_persona != persona

            if mode_changed or persona_changed:
                st.session_state.last_app_mode = app_mode
                st.session_state.previous_persona = persona

                # --- Save Profile for Evaluation ---
                save_user_profile_for_evaluation(
                    username=st.session_state.username,
                    persona=persona,
                    lat=st.session_state.get("lat", -33.8688),
                    lon=st.session_state.get("lon", 151.2093),
                    concern=f"Switched to {persona} mode"
                )
                
                if "assistant" in st.session_state:
                    try:
                        # 1. Update the AI Brain (Switch Context)
                        st.session_state.assistant.update_assistant(target_agent, args={})
                        
                        # 2. ✅ HISTORY PRESERVED: We do NOT clear st.session_state.messages.
                        
                        # 3. ✅ REACTIVE RESPONSE: Inject a message so the AI talks to the user
                        reaction_msg = ""
                        
                        if persona_changed:
                            # Case A: User chose "Other Careers" -> Ask for details
                            if "Other Careers" in persona:
                                reaction_msg = (
                                    "I see you've switched to **Other Careers**. 🎓\n\n"
                                    "To give you the most accurate risk assessment, could you please tell me "
                                    "**what your specific job title or industry is?**\n"
                                    "*(e.g., 'I am a School Principal', 'I manage a large Factory', 'I am a Hospital Admin')*"
                                )
                            # Case B: Standard Role Switch -> Confirm focus
                            else:
                                reaction_msg = (
                                    f"🔄 **Profile Updated: {persona}**\n\n"
                                    "I have adjusted my risk parameters. I am now focused on "
                                    "**financial continuity** and **infrastructure protection** relevant to this role.\n\n"
                                    "What is your primary concern right now?"
                                )
                        elif mode_changed:
                            # Case C: Mode Switch -> Simple acknowledgement
                            reaction_msg = f"✅ Switched to **{app_mode}**. Ready for instructions."

                        # Append to chat history so it appears immediately
                        if reaction_msg:
                            st.session_state.messages.append({"role": "assistant", "content": reaction_msg})

                        # 4. Save Immediately & Rerun
                        session_manager.save_user_session(st.session_state.username)
                        
                        st.toast(f"Context Updated: {persona}", icon="🔄")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Switch Error: {e}")

        # =========================================================
        # --- PART 2: UTILITIES (Always Visible)
        # =========================================================
        st.divider()
        st.caption("⚙️ System Tools")

        # --- FILES ---
        with st.expander("📂 Data & Files"):
            file_manager = FileManager() 
            file_manager.render()

        # --- REPORTS ---
        with st.expander("📄 Report Generation"):
            if "messages" in st.session_state and len(st.session_state.messages) > 0:
                if st.button("Generate PDF Report"):
                    try:
                        pdf_bytes = report.generate_pdf_report(
                            st.session_state.username, 
                            st.session_state.messages
                        )
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=f"Wildfire_Report_{st.session_state.username}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Report Error: {e}")
            else:
                st.info("Chat to generate a report.")

        # --- ACCOUNT SETTINGS ---
        with st.expander("👤 Account Settings"):
            with st.expander("🔑 Change Password"):
                current_password_input = st.text_input("Current Password", type="password", key="curr_pass_input")
                new_password_input = st.text_input("New Password", type="password", key="new_pass_input")
                confirm_password = st.text_input("Confirm New", type="password", key="conf_pass_input")
                
                if st.button("Update Password"):
                    if not auth.verify_login(st.session_state.username, current_password_input):
                        st.error("❌ Current password is incorrect.")
                    elif new_password_input != confirm_password:
                        st.error("⚠️ New passwords do not match.")
                    elif not auth.validate_password(new_password_input):
                        st.error("❌ Password must be at least 6 characters long and contain at least one letter.")
                    else:
                        if auth.change_password(st.session_state.username, new_password_input):
                            st.success("✅ Password updated successfully!")
                        else:
                            st.error("Error updating password.")
            
            with st.expander("🚨 Delete Account"):
                st.warning("This action is permanent.")
                if st.checkbox("Are you sure?"):
                    if st.button("Confirm Deletion", type="primary"):
                        if auth.delete_user(st.session_state.username):
                            # Full Wipe on Delete
                            st.session_state.logged_in = False
                            st.session_state.username = ""
                            if "data_loaded" in st.session_state: del st.session_state["data_loaded"]
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.rerun()

        # --- LOGOUT (FIXED FOR MULTIPLE LOGINS) ---
        st.markdown("---")
        if st.button("Log Out", use_container_width=True):
            # 1. Clear Login Credentials
            st.session_state.logged_in = False
            st.session_state.username = ""
            
            # 2. ✅ CRITICAL FIX: Delete 'data_loaded' flag
            # This ensures that when you log in again, the app knows it needs to 
            # re-fetch your file from the disk.
            if "data_loaded" in st.session_state:
                del st.session_state["data_loaded"]

            # 3. Clear Session Data
            keys_to_clear = [
                "messages", "assistant", "location_confirmed", 
                "lat", "lon", "user_persona", "previous_persona", 
                "pending_file_context", "last_app_mode"
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 4. Restart App
            st.rerun()