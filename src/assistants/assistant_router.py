from src.assistants.profile import ChecklistAssistant
from src.assistants.plan import PlanAssistant
from src.assistants.analyst import AnalystAssistant
import uuid
import streamlit as st

# --- MOCK THREAD CLASS ---
class MockThread:
    """
    A local placeholder for the OpenAI Thread object.
    Since DeepSeek doesn't store threads on the server, we just generate a random ID
    so the rest of the application has a valid 'thread.id' to reference.
    """
    def __init__(self, thread_id=None):
        if thread_id:
            self.id = thread_id
        else:
            self.id = f"local_thread_{str(uuid.uuid4())[:8]}"

class AssistantRouter:
    def __init__(self, name, thread_id=None, args={}):
        
        # --- Local Thread Management ---
        if thread_id:
            self.current_thread = MockThread(thread_id)
            self.new_thread = False
        else:
            self.current_thread = MockThread()
            self.new_thread = True

        # --- append the thread id in `chat_history/threads.txt` ---
        try:
            with open("chat_history/threads.txt", "a") as f:
                f.write(f"{self.current_thread.id}\n")
        except:
            pass  # Silently fail if file doesn't exist
        
        # --- Define assistant mappings to their classes and config paths ---
        self.assistant_dict = {
            "ChecklistAssistant": [ChecklistAssistant, "src/assistants/profile/config.yml"],
            "FollowUpAssistant": [ChecklistAssistant, "src/assistants/profile/config_follow_up.yml"],
            "PlanAssistant": [PlanAssistant, "src/assistants/plan/config.yml"],
            "AnalystAssistant": [AnalystAssistant, "src/assistants/analyst/config.yml"]
        }

        # --- Initialize the assistant based on the provided name ---
        if name in self.assistant_dict:
            AssistantClass = self.assistant_dict[name][0]
            config_path = self.assistant_dict[name][1]
            self.current_assistant = AssistantClass(config_path, self.update_assistant, **args)
        else:
            raise ValueError(f"Unknown assistant name: {name}")

    def update_assistant(self, name, args, new_thread=False):
        """Update to a different assistant type"""
        if name not in self.assistant_dict:
            raise ValueError(f"Unknown assistant name: {name}")
            
        AssistantClass = self.assistant_dict[name][0]
        config_path = self.assistant_dict[name][1]
        self.current_assistant = AssistantClass(config_path, self.update_assistant, **args)
        
        if new_thread:
            # --- Create local MockThread instead of API call ---
            self.current_thread = MockThread()
            try:
                with open("chat_history/threads.txt", "a") as f:
                    f.write(f"{self.current_thread.id}\n")
            except:
                pass
            self.new_thread = True

    # ==========================================
    # --- DEBUG DOCTOR FOR UNPACKING ---
    # ==========================================
    def _debug_assistant_response(self, response_data):
        """
        Debug helper to diagnose assistant response unpacking
        """
        print("🔍 ASSISTANT ROUTER DEBUG:")
        print(f"   Response data type: {type(response_data)}")
        if isinstance(response_data, tuple):
            print(f"   Tuple length: {len(response_data)}")
            for i, item in enumerate(response_data):
                item_type = type(item)
                item_preview = str(item)[:100] if item is not None else "None"
                print(f"   Item {i}: type={item_type}, preview={item_preview}")
        elif isinstance(response_data, list):
            print(f"   List length: {len(response_data)}")
            for i, item in enumerate(response_data[:3]):
                print(f"   Item {i}: type={type(item)}, preview={str(item)[:100]}")
        else:
            print(f"   Value: {str(response_data)[:200]}")
        print("=" * 50)

    def get_assistant_response(self, user_message: str = None):
        """Get response from current assistant with safe context handling"""
        self.new_thread = False
        
        # =========================================================================
        # --- SLIDING WINDOW CONTEXT (Token Saver) ---
        # =========================================================================
        if hasattr(st, 'session_state') and 'messages' in st.session_state:
            real_messages_backup = st.session_state.messages
            is_truncated = False
            
            if len(real_messages_backup) > 6:
                truncated_history = [real_messages_backup[0]] + real_messages_backup[-6:]
                st.session_state.messages = truncated_history
                is_truncated = True
        else:
            real_messages_backup = []
            is_truncated = False
        # =========================================================================

        try:
            # --- CALL THE API ---
            response_data = self.current_assistant.get_assistant_response(user_message, self.current_thread.id)
            
            # --- DEBUG: Show what we received from the assistant before unpacking ---
            self._debug_assistant_response(response_data)
        
            # --- SAFE RESPONSE EXTRACTION ---
            full_response = ""
            
            # --- Handle different return formats ---
            if isinstance(response_data, tuple):
                # --- Extract based on tuple length ---
                if len(response_data) >= 3:
                    # --- Format: (full_response, run_id, tool_outputs) ---
                    full_response = str(response_data[0]) if response_data[0] is not None else ""
                elif len(response_data) == 2:
                    # --- Format: (response, something_else) ---
                    full_response = str(response_data[0]) if response_data[0] is not None else ""
                else:
                    # --- Other tuple format - take first element ---
                    full_response = str(response_data[0]) if len(response_data) > 0 else ""
            elif isinstance(response_data, list):
                # --- List format: [full_response, visualizations] ---
                full_response = str(response_data[0]) if len(response_data) > 0 else ""
            else:
                # --- String or other format ---
                full_response = str(response_data)
            
            # --- Ensure we have at least an empty string ---
            if full_response is None:
                full_response = ""
            
            # --- Handle visualizations ---
            if hasattr(self.current_assistant, 'visualizations') and len(self.current_assistant.visualizations) > 0:
                # --- Return both text and visualizations as a tuple to prevent UI crashes ---
                return [full_response, self.current_assistant.visualizations]
            
            return full_response

        except Exception as e:
            print(f"❌ Error in AssistantRouter.get_assistant_response: {e}")
            return f"Error: {str(e)}"
        finally:
            # =====================================================================
            # --- [CRITICAL RESTORE] UNDO THE SWAP ---
            # =====================================================================
            if hasattr(st, 'session_state') and is_truncated:
                st.session_state.messages = real_messages_backup
            # =====================================================================
    
    def resume_conversation(self):
        """
        DeepSeek does not support retrieving message history from the server.
        This function is disabled to prevent crashes.
        """
        print("Warning: 'Resume Conversation' is not supported with DeepSeek (No server-side thread history).")
        pass