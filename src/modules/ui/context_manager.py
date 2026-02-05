# File: src/utils/context_manager.py

def build_enhanced_prompt(user_prompt, session_state):
    """
    Combines User Question + Business Persona + File Context
    Returns: (final_prompt, visual_badges)
    """
    final_prompt = user_prompt
    active_badges = []
    
    # --- 1. Get Persona (from Sidebar) ---
    current_persona = session_state.get("user_persona", "👨‍🚒 Emergency Commander (Gov)")
    
    # --- 2. Add Persona Instruction (Invisible to user) ---
    if current_persona and "Gov" not in current_persona:
        # --- Enhanced persona instructions with conversation history awareness ---
        conversation_context = ""
        messages = session_state.get("messages", [])
        if len(messages) > 0:
            # --- Get last few messages for context ---
            recent_messages = messages[-4:]  # Last 4 messages
            conv_text = "\n".join([f"{msg['role']}: {msg['content'][:100] if len(str(msg['content'])) > 100 else msg['content']}" 
                                  for msg in recent_messages])
            conversation_context = f"\nRecent conversation context:\n{conv_text}\n"
        
        persona_instruction = (
            f"[SYSTEM INSTRUCTION: The user is currently in '{current_persona}' mode. "
            f"Focus on financial risk, infrastructure protection, and business continuity. "
            f"Remember the conversation history and maintain context. "
            f"Do not ask redundant questions already answered in the conversation.]\n"
            f"{conversation_context}"
        )
        final_prompt = f"{persona_instruction}\n\nUser Question: {user_prompt}"
        active_badges.append(f"👤 {current_persona}")

    # --- 3. Add File Context (from Sidebar Upload) ---
    if session_state.get('pending_file_context'):
        file_name = session_state.get('last_uploaded_filename', 'Attached File')
        # --- Prepend file data to the prompt ---
        final_prompt = f"{session_state['pending_file_context']}\n\n{final_prompt}"
        active_badges.append(f"📎 {file_name}")

    return final_prompt, active_badges