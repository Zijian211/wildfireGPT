import re
import ast
import numpy as np
from scipy.stats import spearmanr

# Define the ANSI escape sequence for purple
PURPLE = '\033[95m'
ENDC = '\033[0m'  # Reset to default color


def normalize_text(text):
    """
    Removes all whitespace, tabs, and newlines.
    Output: "helloworld" for input "hello \n world"
    Usage: Allows matching text even if formatting differs.
    """
    if not text:
        return ""
    
    # --- CRITICAL FIX: Handle Tuple (Text, Visualizations) ---
    if isinstance(text, tuple):
        text = text[0]
        
    return "".join(str(text).split())


def find_previous_user_query(interactions, llm_response_fragment):
    """
    Scans the chat history to find the User prompt that triggered a specific AI response.
    Uses 'fuzzy' matching (ignoring whitespace) to be robust against formatting changes.
    """
    last_user_content = None
    
    if not interactions or not llm_response_fragment:
        return None

    # --- CRITICAL FIX: Handle Tuple ---
    if isinstance(llm_response_fragment, tuple):
        llm_response_fragment = llm_response_fragment[0]

    # Prepare the search fragment (clean up the text we are looking for)
    clean_fragment = normalize_text(llm_response_fragment)
    
    # Safety: If the fragment is tiny (e.g. just "Yes"), don't use it for matching
    if len(clean_fragment) < 5:
        return None

    for entry in interactions:
        if entry['role'] == 'user':
            last_user_content = entry['content']
        elif entry['role'] == 'assistant':
            # --- CRITICAL FIX: Handle Tuple in History ---
            content = entry['content']
            if isinstance(content, tuple):
                content = content[0]

            # Normalize the history content to match the fragment
            clean_content = normalize_text(content)
            
            # Check if our fragment exists inside this history entry
            if clean_fragment in clean_content:
                return last_user_content, entry
                
    return None


def parse_tool_file(content, interactions):
    # Pattern to find sections with correct delimiter
    sections_pattern = r'\*\*Tool Outputs\*\*(.*?)\*\*LLM Response\*\*(.*?)(?=\*\*Tool Outputs\*\*|$)'

    # Find all matches for the sections
    matches = re.findall(sections_pattern, content, flags=re.DOTALL)

    # Process each match to extract Tool Outputs and LLM Response content
    results = []
    for match in matches:
        tool_outputs = "**Tool Outputs**\n" + match[0].strip()
        llm_response = "**LLM Response**\n" + match[1].strip()

        # Only keep the output with '----------' for evaluation
        if '----------' not in tool_outputs:
            continue  # Skip this pair

        # Separate the Instruction and Tool Outputs
        try:
            parts = tool_outputs.split('----------', 1)
            tool_outputs = parts[0].strip()
        except Exception:
            continue

        # Determine the type based on the presence of 'Title' or 'title'
        type_value = 'literature' if 'title:' in tool_outputs.lower() else 'values_and_recommendations'
        
        # --- CRASH PROOFING & ROBUST MATCHING ---
        # 1. Safely extract the first REAL sentence (skipping empty lines)
        response_lines = llm_response.split('\n')
        first_sentence = ""
        
        # Skip the first line (header) and find the first non-empty content line
        for line in response_lines[1:]:
            if line.strip():
                first_sentence = line.strip()
                break
        
        # 2. Safely find the match using normalized text
        search_result = find_previous_user_query(interactions, first_sentence)
        
        # 3. Check if we found anything. If None, skip this entry.
        if search_result is None:
            # print(f"Skipping: Could not link response to chat history.")
            continue
            
        # 4. Unpack safely
        previous_query, current_entry = search_result
        # --- END FIX ---

        # Initialize dictionary for this pair
        entry = {
            'tool_outputs': tool_outputs,
            'llm_response': llm_response,
            'type': type_value,
            'previous_query': previous_query,
            'current_entry': current_entry
        }

        results.append(entry)

    return results


def parse_user_profile(content):
    # Initialize an empty dictionary
    user_profile = {}

    # Split the data into lines
    lines = content.split("\n")

    # Iterate over each line
    for line in lines:
        if ":" in line:  # Check if the line contains a key-value pair
            # Split the line into key and value based on the first colon
            key, value = line.split(":", 1)

            # Clean up the key and value
            key = key.strip().strip('*- ').replace("**", "").lower()  # Remove extra characters and make lowercase
            value = value.replace("**", "").strip()

            # Add the key-value pair to the dictionary
            user_profile[key] = value

    # --- ENHANCEMENT: Extract and normalize profession if not explicitly set ---
    if 'profession' not in user_profile:
        # Try to infer from persona
        if 'persona' in user_profile:
            persona = user_profile['persona']
            if 'Emergency Commander' in persona:
                user_profile['profession'] = 'Emergency Commander (Government)'
            elif 'Insurance Risk Assessor' in persona:
                user_profile['profession'] = 'Insurance Risk Assessor'
            elif 'Power Grid Operator' in persona:
                user_profile['profession'] = 'Power Grid Operator'
            elif 'Logistics Manager' in persona:
                user_profile['profession'] = 'Logistics Manager'
            elif 'Real Estate Developer' in persona:
                user_profile['profession'] = 'Real Estate Developer'
            elif 'Park Ranger' in persona or 'Tourism' in persona:
                user_profile['profession'] = 'Park Ranger / Tourism'
            elif 'Other Careers' in persona:
                user_profile['profession'] = 'Other Professional'
            else:
                user_profile['profession'] = persona
        else:
            user_profile['profession'] = 'Unknown'

    # --- ENHANCEMENT: Ensure location is properly formatted ---
    if 'location' in user_profile and 'lat' not in user_profile:
        # Try to extract lat/lon from location string
        location = user_profile['location']
        if 'latitude' in location.lower() and 'longitude' in location.lower():
            import re
            lat_match = re.search(r'latitude\s*([-\d.]+)', location, re.IGNORECASE)
            lon_match = re.search(r'longitude\s*([-\d.]+)', location, re.IGNORECASE)
            if lat_match and lon_match:
                user_profile['lat'] = float(lat_match.group(1))
                user_profile['lon'] = float(lon_match.group(1))

    return user_profile

def parse_current_entry(entry, aspect):
    return_list = []
    if aspect == 'relevance':
        for key in range(1, 7):
            if f"relevance_feedback_q{key}" in entry.keys():
                return_list.append(entry[f"relevance_feedback_q{key}"])
            else:
                return_list.append('Not Applicable')
    elif aspect == 'accessibility':
        for key in range(1, 4):
            if f"accessibility_feedback_q{key}" in entry.keys():
                if key in [1, 3]:
                    if entry[f"accessibility_feedback_q{key}"] == 'Yes':
                        return_list.append('No')
                    elif entry[f"accessibility_feedback_q{key}"] == 'No':
                        return_list.append('Yes')
                    else:
                        return_list.append(entry[f"accessibility_feedback_q{key}"])
                else:
                    return_list.append(entry[f"accessibility_feedback_q{key}"])
            else:
                return_list.append('Not Applicable')
    elif aspect == 'entailment':
        for key in range(1, 2):
            if f"entailment_feedback_q{key}" in entry.keys():
                return_list.append(entry[f"entailment_feedback_q{key}"])
            else:
                return_list.append('Not Applicable')
    
    return return_list
            

def convert_scores(input_score, aspect):
    # --- FIX FOR CLOUD/LLAMA-3: CLEAN MARKDOWN ---
    # Llama-3 often wraps output in ```python ... ```
    input_score = re.sub(r"```python", "", str(input_score)) # Ensure string input
    input_score = re.sub(r"```", "", input_score).strip()
    # ---------------------------------------------

    # Regular expression to match all reasoning blocks
    print(f"{PURPLE}response{ENDC}", input_score)
    reasonings = re.findall(r'\(\d+\)\s+(.*?)\n\n', input_score, re.DOTALL)
    
    # Fallback: if regex finds nothing (e.g. Llama-3 wrote an essay), use the whole text as reasoning
    if not reasonings:
        reasonings = [str(input_score)]

    # Check if input_score is a string that contains a list or tuple structure
    if isinstance(input_score, str) and ("[" in input_score or "(" in input_score):
        # Clean up string if necessary
        if "[" in input_score and "]" in input_score:
            input_score = input_score[input_score.index("["):input_score.rindex("]") + 1]
        
        try:
            # Try to convert the input string to a list/tuple directly
            input_score = ast.literal_eval(input_score)
        except (ValueError, SyntaxError):
            # Fallback formatting
            input_score = re.sub(r"(?<=\[|\s|,)([^\\d\\[\\]'\"].*?)(?=,|\])", r"'\1'", input_score)
            try:
                input_score = ast.literal_eval(input_score)
            except (ValueError, SyntaxError) as e:
                print(f"Error in converting input_score: {e}")
                # --- CRITICAL FIX: Return a tuple (list, string) to prevent crash ---
                # We return a list of "Error" so the UI displays it safely
                return ["Error Parsing"], str(input_score)

    # --- CRITICAL FIX START ---
    # If it is a tuple, convert it to a list so we can modify it later
    if isinstance(input_score, tuple):
        input_score = list(input_score)
    # --- CRITICAL FIX END ---

    # print the type of input_score to debug
    print(f"{PURPLE}input_score{ENDC}", input_score)

    if aspect in ['correctness']:
        scores = re.findall(r"(\d+)/(\d+)", str(input_score))
        if len(scores) > 0:
            matches, total = map(int, scores[0])
        else:
            matches = total = 0
        return matches, reasonings, total, 0, input_score

    else:
        # 1. Handle Accessibility logic (3 items) - NOW SAFE because it is a list
        if isinstance(input_score, list) and len(input_score) == 3:
            for i in [0, 2]:
                input_score[i] = 'No' if input_score[i] == 'Yes' else 'Yes'
        
        # 2. Handle Single Item List
        if isinstance(input_score, list) and len(input_score) == 1:
            input_score = input_score[0]
            
        return input_score, reasonings
    
if __name__ == '__main__':
    print(convert_scores("Yes, 0/8", "correctness"))