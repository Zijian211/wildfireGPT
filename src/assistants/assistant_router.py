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
    def __init__(self, name, thread_id = None, args={}):
        
        # --- Local Thread Management ---
        if thread_id:
            self.current_thread = MockThread(thread_id)
            self.new_thread = False
        else:
            self.current_thread = MockThread()
            self.new_thread = True

        # --- append the thread id in `chat_history/threads.txt` ---
        with open("chat_history/threads.txt", "a") as f:
            f.write(f"{self.current_thread.id}\n")
        
        self.assistant_dict = {
            "ChecklistAssistant": [ChecklistAssistant, "src/assistants/profile/config.yml"],
            "FollowUpAssistant": [ChecklistAssistant, "src/assistants/profile/config_follow_up.yml"],
            "PlanAssistant": [PlanAssistant, "src/assistants/plan/config.yml"],
            "AnalystAssistant": [AnalystAssistant, "src/assistants/analyst/config.yml"]
        }

        Assistant = self.assistant_dict[name][0]
        config_path = self.assistant_dict[name][1]
        self.current_assistant = Assistant(config_path, self.update_assistant, **args)

    def update_assistant(self, name, args, new_thread = False):
        Assistant = self.assistant_dict[name][0]
        config_path = self.assistant_dict[name][1]
        self.current_assistant = Assistant(config_path, self.update_assistant, **args)
        
        if new_thread:
            # --- Create local MockThread instead of API call ---
            self.current_thread = MockThread()
            with open("chat_history/threads.txt", "a") as f:
                f.write(f"{self.current_thread.id}\n")
            self.new_thread = True

    def get_assistant_response(self, user_message: str = None):
        self.new_thread = False
        
        # =========================================================================
        # SLIDING WINDOW CONTEXT (Token Saver)
        # =========================================================================
        # --- The sub-assistants read `st.session_state.messages` to build the prompt ---
        # --- If we send the full history (20+ msgs), we hit Rate Limits immediately ---
        # --- This block forces the Assistant to see only the last 6 messages ---
        
        real_messages_backup = st.session_state.messages
        is_truncated = False
        
        # --- Check if history is long enough to need truncation ---
        if len(real_messages_backup) > 6:
            # --- 1. Keep System Prompt (Index 0 - The "Brain") and Keep Last 6 Messages (Short-term Memory) ---
            truncated_history = [real_messages_backup[0]] + real_messages_backup[-6:]
            
            # --- 2. SWAP: Temporarily replace session state with short version ---
            st.session_state.messages = truncated_history
            is_truncated = True
        # =========================================================================

        try:
            # --- CALL THE API ---
            # --- The assistant now reads the short `st.session_state.messages` list ---
            # --- This payload is small (~500 tokens) ---
            full_response, run_id, tool_outputs = self.current_assistant.get_assistant_response(user_message, self.current_thread.id)
            
            if len(tool_outputs):
                full_response += "\n\n"
                full_response += self.current_assistant.respond_to_tool_output(self.current_thread.id, run_id, tool_outputs)
            elif self.new_thread:
                # --- Recursively call if thread changed ---
                # --- The `finally` block will handle restoration before the recursive call returns ---
                return self.get_assistant_response()
                
            if hasattr(self.current_assistant, 'visualizations') and len(self.current_assistant.visualizations) > 0:
                full_response = [full_response, self.current_assistant.visualizations]
                self.current_assistant.visualizations = []
                
            return full_response

        finally:
            # =====================================================================
            # [CRITICAL RESTORE] UNDO THE SWAP
            # =====================================================================
            # --- We MUST restore the original full history immediately ---
            # --- If we don't do this, the UI will "forget" the old messages ---
            if is_truncated:
                st.session_state.messages = real_messages_backup
            # =====================================================================
    
    def resume_conversation(self):
        """
        DeepSeek does not support retrieving message history from the server.
        This function is disabled to prevent crashes.
        """
        print("Warning: 'Resume Conversation' is not supported with DeepSeek (No server-side thread history).")
        pass
            
