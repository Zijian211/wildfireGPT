""""
Offline Evaluation Script for WildfireGPT.
This script evaluates the performance of the LLM by comparing its responses
against human-annotated guidelines and correctness metrics.
"""

import os
import json
import argparse
import yaml
import pandas as pd
import streamlit as st
from tqdm import tqdm
from typing import List, Dict, Any, Optional

# --- Local Imports ---
from src.evaluation.utils import (
    parse_tool_file,
    parse_user_profile,
    convert_scores,
    parse_current_entry
)
from src.evaluation.prompts import Prompts
from src.evaluation.auto import score_sbert_similarity

# --- IMPORT CLIENT AND CONFIG_MODEL FROM YOUR CONFIG FILE ---
from src.config import client, model as config_model

# --- Define colors for logging ---
PURPLE = '\033[95m'
ENDC = '\033[0m'

class Evaluator:
    """
    Handles the offline evaluation of LLM interactions.
    """

    def __init__(self, args: Dict[str, Any]):
        self.args = args
        self.prompts = Prompts()
        
        # ---Normalize path for Windows Localhost ---
        raw_case = args.get('case_folder')
        # This combines mixed slashes in Cloud/Localhost paths
        if raw_case:
            self.case = os.path.normpath(raw_case) 
        else:
            self.case = raw_case
        self.debug_path = os.path.join(self.case, "debug_log.txt")
        
        # --- Model Configuration ---
        self.client = client

        # --- Smart Model Selection (Cloud vs Local) ---
        try:
            base_url_str = str(self.client.base_url)
            if "groq.com" in base_url_str or "localhost" in base_url_str:
                print(f"☁️ Cloud/Local Mode Detected: Forcing model to '{config_model}'")
                self._log(f"Mode: Cloud/Local ({config_model})")
                self.model_name = config_model
            else:
                self.model_name = args.get('llm_model') or config_model
        except Exception:
            self.model_name = args.get('llm_model') or config_model

        # --- Load Data ---
        self._log(f"Initializing evaluation for: {self.case}")
        self.interaction_history = self._load_interaction_history()
        
        # --- The loader handles cases where tools.txt is missing/empty ---
        self.data_dict = self._load_data_robust() 
        
        # --- SMART PROFILE LOADING (Auto-Discovery) ---
        self.user_profile = self._load_user_profile_smart()

    def _log(self, msg):
        """Helper to write debug info."""
        try:
            with open(self.debug_path, "a", encoding="utf-8") as f:
                f.write(str(msg) + "\n")
        except:
            pass

    def _load_interaction_history(self) -> List[Dict]:
        """Loads the chat history from interaction.jsonl."""
        file_path = os.path.join(self.case, "interaction.jsonl")
        history = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        history.append(json.loads(line))
            self._log(f"Loaded {len(history)} interaction lines.")
        except FileNotFoundError:
            self._log(f"Warning: Could not find interaction.jsonl in {self.case}")
        return history

    def _load_data_robust(self) -> List[Dict]:
        """
        Attempts to load tool outputs. If tools.txt is empty/missing,
        falls back to creating data items directly from interaction history.
        """
        # --- 1. Try loading standard tools.txt ---
        file_path = os.path.join(self.case, "tools.txt")
        parsed_data = []
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        parsed_data = parse_tool_file(content, self.interaction_history)
                        self._log(f"Loaded {len(parsed_data)} items from tools.txt")

            # --- 2. FALLBACK: If tools.txt yielded nothing, use Chat History ---
            if not parsed_data and self.interaction_history:
                self._log("Tools data empty. Falling back to Chat History parsing.")
                
                for i, entry in enumerate(self.interaction_history):
                    if entry.get('role') == 'assistant':
                        # --- Find the user query that triggered this ---
                        prev_query = "Start of conversation"
                        if i > 0 and self.interaction_history[i-1].get('role') == 'user':
                            prev_query = self.interaction_history[i-1].get('content', '')

                        # --- Create a standardized entry object ---
                        item = {
                            "tool_outputs": "Direct Chat (No Tools)", # Placeholder
                            "llm_response": entry.get('content', ''),
                            "previous_query": prev_query,
                            "type": "general",
                            "current_entry": entry # Used for human_score parsing
                        }
                        parsed_data.append(item)
                
                self._log(f"Generated {len(parsed_data)} evaluation items from Chat History.")
                
        except Exception as e:
            self._log(f"Error loading data: {e}")
            
        return parsed_data

    # --- AUTO-DISCOVER PROFILE ---
    def infer_profile_from_history(self, interactions):
        """
        If user_profile.txt is missing, this function asks the LLM 
        to read the chat history and figure out who the user is.
        """
        print(f"{PURPLE}Generating User Profile from Chat History...{ENDC}")
        self._log("Generating User Profile from Chat History...")
        
        # --- 1. Convert chat history to a single string ---
        chat_text = ""
        for turn in interactions:
            role = turn.get('role', 'unknown').upper()
            content = turn.get('content', '')
            chat_text += f"{role}: {content}\n"
        
        # --- 2. Create a prompt for the LLM ---
        prompt = (
            "You are an expert summarizer. Read the following chat history and extract "
            "the User's profile information to help with evaluation.\n"
            "Format the output EXACTLY like this:\n"
            "Name: [Name]\n"
            "Location: [Location]\n"
            "Concern: [Concern]\n"
            "Timeline: [Timeline]\n"
            "Profession: [Profession]\n\n"
            "If information is missing, write 'Unknown'.\n\n"
            f"Chat History:\n{chat_text}"
        )

        # --- 3. Call the LLM ---
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            self._log(f"Error inferring profile: {e}")
            return "Name: Unknown\nLocation: Unknown"

    def _load_user_profile_smart(self) -> Dict:
        """
        Smart loader that auto-generates profile if missing.
        """
        file_path = os.path.join(self.case, "user_profile.txt")
        user_profile_content = ""

        # --- 1. Try to load manual file ---
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                user_profile_content = f.read()
        
        # --- 2. If missing/empty, Auto-Generate ---
        if not user_profile_content or len(user_profile_content) < 10:
            if self.interaction_history:
                user_profile_content = self.infer_profile_from_history(self.interaction_history)
                # --- Try saving it for reference ---
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(user_profile_content)
                except:
                    pass
            else:
                user_profile_content = "Name: Unknown"

        self._log(f"Active User Profile: {user_profile_content[:100]}...")
        return parse_user_profile(user_profile_content)

    # --- KEEPING OLD LOADER FOR BACKWARD COMPATIBILITY IF NEEDED ---
    def _load_user_profile(self) -> Dict:
        return self._load_user_profile_smart()

    def generate_eval_response(self, messages_list: List[str]) -> Optional[str]:
        """Simulates the Assistant flow using standard Chat Completions."""
        if not messages_list:
            return None

        history = [
            {"role": "system", "content": messages_list[0]},
            {"role": "user", "content": messages_list[1]}
        ]

        try:
            # --- Turn 1 for Single or Multi-turn ---
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=history,
                temperature=0.0
            )
            reply_text = response.choices[0].message.content

            # --- Turn 2 (if prompt requires it) ---
            if len(messages_list) > 2:
                history.append({"role": "assistant", "content": reply_text})
                history.append({"role": "user", "content": messages_list[2]})
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=history,
                    temperature=0.0
                )
                reply_text = response.choices[0].message.content
            
            return reply_text

        except Exception as e:
            self._log(f"API Error: {e}")
            return None

    def evaluate_single_aspect(self, tool_outputs, llm_response, data_type, previous_query, aspect):
        """Uses prompts.py logic to generate the evaluation prompt."""
        prompt_method_name = (
            f'evaluate_{aspect}_in_reference' if data_type == 'literature'
            else f'evaluate_{aspect}_in_values_and_recommendations'
        )
        
        prompt_method = getattr(self.prompts, prompt_method_name, None)
        if not prompt_method:
            # --- Fallback for aspects not in prompts.py ---
            return None

        # --- Build context for the prompt ---
        messages = prompt_method(tool_outputs, llm_response, self.user_profile, previous_query)
        return self.generate_eval_response(messages)

    def llm_evaluate(self):
        """
        Main evaluation loop.
        """
        print(f"Starting evaluation using model: {self.model_name}")
        self._log("Starting llm_evaluate loop...")
        
        # --- Define Columns matching your desired CSV format ---
        df = pd.DataFrame(columns=['case', 'aspect', 'human_score', 'input_score', 'reasoning'])

        if not self.data_dict:
            self._log("Data dict empty. Writing empty CSV.")
            df.to_csv(os.path.join(self.case, 'evaluation.csv'), index=False)
            return

        # --- Iterate over every interaction turn ---
        for i, data in enumerate(tqdm(self.data_dict, desc="Evaluating")):
            tool_outputs = data.get('tool_outputs', '')
            llm_response = data.get('llm_response', '')
            data_type = data.get('type', 'general')
            previous_query = data.get('previous_query', '')
            current_entry = data.get('current_entry', {})

            # --- 1. Evaluate Qualitative Aspects (Relevance, Entailment, Accessibility) ---
            for aspect in ['relevance', 'entailment', 'accessibility']:
                
                human_score = parse_current_entry(current_entry, aspect)
                
                # --- Call the specific prompt from prompts.py ---
                response = self.evaluate_single_aspect(tool_outputs, llm_response, data_type, previous_query, aspect)
                
                if response:
                    # --- Use utils.py to parse the "Yes/No" list output ---
                    input_score, reasonings = convert_scores(response, aspect)

                    # --- Logic to format lists for CSV rows ---
                    target_len = len(input_score) if isinstance(input_score, list) else 1
                    
                    # --- Normalize input_score to list ---
                    if not isinstance(input_score, list): input_score = [input_score]
                    # --- Normalize reasonings to list ---
                    if not isinstance(reasonings, list): reasonings = [str(reasonings)]
                    # --- Normalize human_score to list ---
                    if not human_score: human_score = ["N/A"] * target_len

                    # --- Pad lists to ensure they are equal length ---
                    input_score = (input_score + ["Error"] * target_len)[:target_len]
                    reasonings = (reasonings + [""] * target_len)[:target_len]
                    human_score = (human_score + ["N/A"] * target_len)[:target_len]

                    # --- Add rows to DataFrame ---
                    new_row = pd.DataFrame({
                        'case': [f"turn_{i}"] * target_len, # --- Using turn number as case ID ---
                        'aspect': [aspect] * target_len,
                        'human_score': human_score,
                        'input_score': input_score,
                        'reasoning': reasonings
                    })
                    df = pd.concat([df, new_row], ignore_index=True)
                else:
                    self._log(f"Failed to get response for {aspect} on turn {i}")

        # --- Save CSV ---
        csv_path = os.path.join(self.case, 'evaluation.csv')
        df.to_csv(csv_path, index=False)
        
        # --- Save Data Dict (for manual review) ---
        json_path = os.path.join(self.case, 'data_dict.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data_dict, f, indent=4)

        print(f"Evaluation complete. Results saved to {csv_path}")
        self._log("Evaluation finished successfully.")

if __name__ == "__main__":
    # --- Standard CLI entry point ---
    config_args = {}
    try:
        with open('src/evaluation/config.yaml', 'r') as file:
            config_args = yaml.safe_load(file) or {}
    except FileNotFoundError:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--case_folder', type=str, default=None)
    parser.add_argument('--verbose', action='store_true')
    
    cmd_args = parser.parse_args()

    final_args = {
        'llm_model': cmd_args.model or config_args.get('llm_model') or config_model,
        'case_folder': cmd_args.case_folder or config_args.get('case_folder'),
        'verbose': cmd_args.verbose
    }

    if final_args['case_folder']:
        evaluator = Evaluator(final_args)
        evaluator.llm_evaluate()
    else:
        print("Please provide --case_folder")