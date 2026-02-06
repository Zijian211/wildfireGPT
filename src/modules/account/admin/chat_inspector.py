import streamlit as st
import os
import pickle
import glob

def render_chat_inspector_tab():
    """
    Chat Inspector Tab - Extracted from admin_page.py
    """
    st.subheader("🔍 Inspect User Sessions")
    st.info("View user chat history safely (Maps/Images are hidden to prevent crashes).")

    history_dir = "chat_history"
    if not os.path.exists(history_dir):
        st.warning("No chat history folder found.")
    else:
        # --- Find all session files ---
        files = glob.glob(os.path.join(history_dir, "*_session_state.pkl"))
        users_with_history = [os.path.basename(f).replace("_session_state.pkl", "") for f in files]

        if not users_with_history:
            st.info("No active sessions found.")
        else:
            selected_user_chat = st.selectbox("Select User:", users_with_history, key="inspect_user_select")
            
            if selected_user_chat:
                file_path = os.path.join(history_dir, f"{selected_user_chat}_session_state.pkl")
                try:
                    # --- Check if file exists and has content ---
                    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        st.warning(f"Session file for {selected_user_chat} is empty or corrupted.")
                    else:
                        with open(file_path, "rb") as f:
                            # --- Safe Pickle Load ---
                            try:
                                session_data = pickle.load(f)
                            except AttributeError:
                                # --- Fallback if AssistantRouter class isn't imported ---
                                st.warning("⚠️ Some session objects could not be loaded. Showing raw text only.")
                                session_data = {"messages": [], "user_persona": "Unknown"}
                            except Exception as e:
                                st.error(f"Error loading pickle file: {e}")
                                session_data = {"messages": [], "user_persona": "Unknown"}

                        # --- Display Metadata ---
                        st.caption(f"Role: **{session_data.get('user_persona', 'Unknown')}** | " 
                                  f"Lat: {session_data.get('lat', 'N/A')} | "
                                  f"Lon: {session_data.get('lon', 'N/A')}")
                        st.divider()

                        # --- Render Messages Safely ---
                        messages = session_data.get("messages", [])
                        if not messages:
                            st.info("No chat messages found in this session.")
                        else:
                            for msg in messages:
                                role = msg.get("role", "unknown")
                                content = msg.get("content", "")
                                
                                with st.chat_message(role):
                                    # --- Handle Tuples (Text, Map) ---
                                    if isinstance(content, tuple):
                                        st.markdown(content[0]) # Display text only
                                        st.caption("*(Interactive Map/Chart Hidden in Admin View)*")
                                    else:
                                        st.markdown(content)
                                    
                except Exception as e:
                    st.error(f"Could not load session: {e}")