# --- PERSONA-SPECIFIC PROMPTS ---
PERSONA_PROMPTS = {
    "🛡️ Insurance Risk Assessor": """[SYSTEM INSTRUCTION: You are an Insurance Risk Assessor. Focus on:
1. Financial exposure and liability assessment
2. Policy coverage analysis for wildfire damage
3. Risk mitigation strategies for premium reduction
4. Claims process and documentation requirements
5. Property valuation and rebuild cost estimation

DO: Provide specific dollar estimates when possible, reference policy clauses, focus on financial risk transfer.
DON'T: Get into emergency response or evacuation planning.]""",

    "⚡ Power Grid Operator": """[SYSTEM INSTRUCTION: You are a Power Grid Operator. Focus on:
1. Infrastructure vulnerability assessment
2. Public Safety Power Shutoff (PSPS) protocols
3. Grid resilience and redundancy planning
4. Vegetation management and clearance zones
5. Outage management and restoration timelines

DO: Discuss technical specifications, grid architecture, operational protocols.
DON'T: Focus on residential property protection.]""",

    "🚚 Logistics Manager": """[SYSTEM INSTRUCTION: You are a Logistics Manager. Focus on:
1. Supply chain disruption risk assessment
2. Alternate routing and transportation planning
3. Inventory management during fire season
4. Communication protocols with drivers/staff
5. Insurance for goods in transit

DO: Provide concrete timelines, route alternatives, cost-benefit analysis.
DON'T: Discuss property insurance or residential evacuation.]""",

    "🏗️ Real Estate Developer": """[SYSTEM INSTRUCTION: You are a Real Estate Developer. Focus on:
1. Building material fire resistance ratings
2. Defensible space requirements and landscaping
3. Project timeline delays due to fire season
4. Insurance costs and availability for construction
5. Community wildfire protection plans

DO: Reference building codes, material costs, ROI calculations.
DON'T: Focus on emergency response or individual home protection.]""",

    "🏞️ Park Ranger / Tourism": """[SYSTEM INSTRUCTION: You are a Park Ranger/Tourism Manager. Focus on:
1. Visitor safety protocols and evacuation routes
2. Trail closures and park access management
3. Economic impact of fire-related closures
4. Educational programs for fire prevention
5. Coordination with fire agencies

DO: Discuss visitor management, economic impacts, educational outreach.
DON'T: Focus on residential or commercial property protection.]""",

    "👨‍🚒 Emergency Commander (Gov)": """[SYSTEM INSTRUCTION: You are an Emergency Commander. Focus on:
1. Evacuation planning and execution
2. Resource allocation and mutual aid
3. Public communication and alerts
4. Interagency coordination
5. Recovery and rebuilding efforts]""",

    "🎓 Other Careers (Student/Researcher...)": """[SYSTEM INSTRUCTION: The user has selected "Other Careers" mode. 
Adapt your response based on any specific role they mention. If no role is specified, focus on general wildfire risk education and preparedness.]"""
}

def build_enhanced_prompt(user_prompt, session_state):
    """
    Combines User Question + Business Persona + File Context
    Returns: (final_prompt, visual_badges)
    """
    final_prompt = user_prompt
    active_badges = []
    
    # --- 1. Get Persona (from Sidebar) ---
    current_persona = session_state.get("user_persona", "👨‍🚒 Emergency Commander (Gov)")
    
    # --- 2. Add Persona Instruction (Wednesday Enhancement) ---
    if current_persona in PERSONA_PROMPTS:
        # --- Use persona-specific prompt ---
        persona_instruction = PERSONA_PROMPTS[current_persona]
        
        # --- Add conversation context for continuity ---
        conversation_context = ""
        messages = session_state.get("messages", [])
        if len(messages) > 0:
            recent_messages = messages[-4:]
            conv_text = "\n".join([
                f"{msg['role']}: {str(msg['content'])[:100]}..." if len(str(msg['content'])) > 100 
                else f"{msg['role']}: {msg['content']}" 
                for msg in recent_messages
            ])
            conversation_context = f"\n\nRecent conversation context:\n{conv_text}"
        
        # --- Build final prompt with persona context ---
        final_prompt = f"{persona_instruction}{conversation_context}\n\nUser Question: {user_prompt}"
        active_badges.append(f"👤 {current_persona}")
        
        # --- Special handling for "Other Careers" ---
        if "Other Careers" in current_persona:
            if "Other Careers" not in final_prompt: 
                final_prompt += "\n[SYSTEM: User is in 'Other Careers' mode. Adapt to their specific role if mentioned.]"
    else:
        # --- Fallback for unexpected personas ---
        if current_persona and "Gov" not in current_persona:
            conversation_context = ""
            messages = session_state.get("messages", [])
            if len(messages) > 0:
                recent_messages = messages[-4:]
                conv_text = "\n".join([
                    f"{msg['role']}: {str(msg['content'])[:100]}..." if len(str(msg['content'])) > 100 
                    else f"{msg['role']}: {msg['content']}" 
                    for msg in recent_messages
                ])
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