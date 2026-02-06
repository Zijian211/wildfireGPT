import os
import json
import datetime
import re

def extract_profession_from_persona(persona):
    """Extracts standardized profession from persona string."""
    if "Emergency Commander" in persona:
        return "Emergency Commander (Government)"
    elif "Insurance Risk Assessor" in persona:
        return "Insurance Risk Assessor"
    elif "Power Grid Operator" in persona:
        return "Power Grid Operator"
    elif "Logistics Manager" in persona:
        return "Logistics Manager"
    elif "Real Estate Developer" in persona:
        return "Real Estate Developer"
    elif "Park Ranger" in persona or "Tourism" in persona:
        return "Park Ranger / Tourism"
    elif "Other Careers" in persona:
        return "Other Professional"
    else:
        # --- Remove emojis and extra characters for unknown professions ---
        import re
        return re.sub(r'[^\w\s\-\(\)]', '', persona).strip()

def save_user_profile_for_evaluation(username, persona, lat, lon, concern="", timeline=""):
    """
    Saves a comprehensive user profile for evaluation purposes.
    """
    profile_dir = "chat_history"
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    
    profile_path = os.path.join(profile_dir, f"{username}_eval_profile.json")
    
    # --- Remove emojis from persona for text storage ---
    import re
    # --- Simple emoji removal ---
    persona_no_emoji = re.sub(r'[^\w\s\-\(\)]', '', persona).strip()
    
    profile_data = {
        "username": username,
        "persona": persona,
        "persona_clean": persona_no_emoji,
        "location": {
            "lat": lat,
            "lon": lon
        },
        "concern": concern,
        "timeline": timeline,
        "profession": extract_profession_from_persona(persona),
        "created_at": datetime.datetime.now().isoformat()
    }
    
    # --- Save JSON with UTF-8 (handles emojis) ---
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)
    
    # --- Also create a text version WITHOUT emojis for easier reading in evaluation ---
    text_profile_path = os.path.join(profile_dir, f"{username}_profile.txt")
    
    with open(text_profile_path, "w", encoding="utf-8") as f:
        f.write(f"User: {username}\n")
        f.write(f"Persona: {persona_no_emoji}\n")
        f.write(f"Profession: {extract_profession_from_persona(persona)}\n")
        f.write(f"Location: Latitude {lat}, Longitude {lon}\n")
        f.write(f"Concern: {concern}\n")
        f.write(f"Timeline: {timeline}\n")
    
    return profile_path