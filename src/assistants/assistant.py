import streamlit as st
import json
from abc import ABC, abstractmethod
from src.utils import get_assistant, load_config, TEXT_CURSOR
from src.config import client, model

class Assistant(ABC):
    def __init__(self, config_path, update_assistant):
        self.config = load_config(config_path)
        self.function_dict = {}
        self.update_assistant = update_assistant
        
        # Initialize the 'Mock' assistant (from your modified utils.py)
        self.assistant = get_assistant(self.config, self.initialize_instructions)
        
        # Initialize local history because DeepSeek is stateless
        # We start with the system instructions
        self.history = [{"role": "system", "content": self.assistant.instructions}]
        self.visualizations = []
    
    @abstractmethod
    def initialize_instructions(self):
        pass
    
    def get_assistant_response(self, user_message=None, thread_id=None):
        """
        Replaces the complex 'Run' logic with a simple Chat Completion stream.
        """
        
        # --- SAFETY CHECK: Auto-initialize history if missing (Fixes AttributeError) ---
        if not hasattr(self, 'history'):
            # Recover instructions if history was lost or not initialized by subclass
            inst = self.assistant.instructions if hasattr(self, 'assistant') else "You are a helpful assistant."
            self.history = [{"role": "system", "content": inst}]
        # -----------------------------------------------------------------------------

        # Add the User's message to our local history
        if user_message:
            self.history.append({"role": "user", "content": user_message})

        # Create the Stream using DeepSeek (Standard Chat API) -- use the 'model' variable imported from src.config
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=self.history,
                stream=True,
                temperature=0.7
            )
        except Exception as e:
            st.error(f"Error calling DeepSeek: {e}")
            return "Error connecting to API.", None, []

        # Handle the Stream and Update the UI
        full_response = ""
        message_placeholder = st.empty()
        
        for chunk in stream:
            # Extract content from the standard chunk format
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                # Update the Streamlit UI in real-time
                message_placeholder.markdown(full_response + TEXT_CURSOR)
        
        # Final update to remove the cursor
        message_placeholder.markdown(full_response)
        
        # Add the Assistant's response to history
        self.history.append({"role": "assistant", "content": full_response})

        # Return the tuple expected by the Router
        # (Response Text, Run ID, Tool Outputs)
        # We return None/[] because we aren't using the complex Run/Tool system.
        return full_response, None, []

    def respond_to_tool_output(self, thread_id, run_id, tool_outputs):
        """
        DeepSeek does not support the server-side 'submit_tool_outputs' flow, so the file pass this to prevent crashes if the router calls it.
        """
        return ""

    def add_assistant_message(self, message, thread_id):
        """
        Manually add a message to history if needed.
        """
        # --- SAFETY CHECK ---
        if not hasattr(self, 'history'):
            inst = self.assistant.instructions if hasattr(self, 'assistant') else "You are a helpful assistant."
            self.history = [{"role": "system", "content": inst}]
        # --------------------
        
        self.history.append({"role": "assistant", "content": message})

    def stream_output(self, stream):
        pass

    def on_tool_call_created(self, tool):
        pass