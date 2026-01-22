"""
Offline Evaluation Script for WildfireGPT.
This script evaluates the performance of the LLM by comparing its responses
against human-annotated guidelines and correctness metrics.
"""

import os
import json
import argparse
import yaml
import torch
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


class Evaluator:
    """
    Handles the offline evaluation of LLM interactions.
    """

    def __init__(self, args: Dict[str, Any]):
        self.args = args
        self.prompts = Prompts()
        self.case = args.get('case_folder')
        
        # --- Model Configuration (FIXED) ---
        # --- 1. Store the client explicitly from config.py ---
        self.client = client

        # --- 2. Smart Model Selection ---
        
        base_url_str = str(self.client.base_url)
        
        if "groq.com" in base_url_str or "localhost" in base_url_str:
            # --- We are in Cloud (Groq) or Localhost (LM Studio) ---
            print(f"☁️ Cloud/Local Mode Detected: Forcing model to '{config_model}'")
            self.model_name = config_model
        else:
            # --- Use arg if provided, else default ---
            self.model_name = args.get('llm_model') or config_model

        # --- Load Data ---
        self.interaction_history = self._load_interaction_history()
        self.data_dict = self._load_tool_outputs()
        self.user_profile = self._load_user_profile()

        # --- Initialize Score Tracking ---
        self.scores = {
            'relevance_score': 0, 'correctness_score': 0, 'entailment_score': 0,
            'accessibility_score': 0, 'relevance_total': 0, 'correctness_total': 0,
            'entailment_total': 0, 'accessibility_total': 0,
            'relevance_na': 0, 'correctness_na': 0, 'entailment_na': 0,
            'accessibility_na': 0
        }

    def _load_interaction_history(self) -> List[Dict]:
        """Loads the chat history from interaction.jsonl."""
        file_path = os.path.join(self.case, "interaction.jsonl")
        history = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    history.append(json.loads(line))
        except FileNotFoundError:
            print(f"Warning: Could not find interaction.jsonl in {self.case}")
        return history

    def _load_tool_outputs(self) -> List[Dict]:
        """Loads and parses the tool outputs from tools.txt."""
        file_path = os.path.join(self.case, "tools.txt")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return parse_tool_file(content, self.interaction_history)
        except FileNotFoundError:
            print(f"Warning: Could not find tools.txt in {self.case}")
            return []

    def _load_user_profile(self) -> Dict:
        """Loads the user profile from user_profile.txt."""
        file_path = os.path.join(self.case, "user_profile.txt")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return parse_user_profile(f.read())
        except FileNotFoundError:
            return {}

    def generate_eval_response(self, messages_list: List[str]) -> Optional[str]:
        """
        Simulates the Assistant flow using standard Chat Completions.
        """
        if not messages_list:
            return None

        history = [
            {"role": "system", "content": messages_list[0]},
            {"role": "user", "content": messages_list[1]}
        ]

        try:
            # --- Turn 1 ---
            # --- USE self.client HERE (from config.py) ---
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=history,
                temperature=0.1 
            )
            reply_text = response.choices[0].message.content

            # --- Turn 2 (if follow-up exists) ---
            if len(messages_list) > 2:
                history.append({"role": "assistant", "content": reply_text})
                history.append({"role": "user", "content": messages_list[2]})
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=history,
                    temperature=0.1
                )
                reply_text = response.choices[0].message.content
            
            return reply_text

        except Exception as e:
            print(f"Error generating evaluation: {e}")
            return None

    def evaluate_single_aspect(self, tool_outputs, llm_response, data_type, previous_query, aspect):
        """Generates the prompt and queries the LLM for a specific aspect."""
        # --- Dynamically fetch the correct prompt method based on data type ---
        prompt_method_name = (
            f'evaluate_{aspect}_in_reference' if data_type == 'literature'
            else f'evaluate_{aspect}_in_values_and_recommendations'
        )
        
        prompt_method = getattr(self.prompts, prompt_method_name, None)
        if not prompt_method:
            print(f"Error: Prompt method {prompt_method_name} not found.")
            return None

        messages = prompt_method(tool_outputs, llm_response, self.user_profile, previous_query)
        return self.generate_eval_response(messages)

    def automatic_eval_for_literature(self, tool_outputs, llm_response):
        """Calculates semantic similarity using SBERT."""
        return score_sbert_similarity(tool_outputs, llm_response)

    def llm_evaluate(self):
        """
        Main evaluation loop. Iterates through data and saves results to CSV.
        """
        print(f"Starting evaluation using model: {self.model_name}")
        
        # --- Columns for the report ---
        df = pd.DataFrame(columns=['case', 'aspect', 'human_score', 'input_score', 'reasoning'])

        if not self.data_dict:
            print("No data found to evaluate.")
            return

        for data in tqdm(self.data_dict, desc="Evaluating"):
            tool_outputs = data.get('tool_outputs', '')
            llm_response = data.get('llm_response', '')
            data_type = data.get('type', 'general')
            previous_query = data.get('previous_query', '')
            current_entry = data.get('current_entry', {})

            # --- Evaluate Qualitative Aspects ---
            for aspect in ['relevance', 'entailment', 'accessibility']:
                human_score = parse_current_entry(current_entry, aspect)
                
                # --- valid_human_scores = [s for s in human_score if s != 'Not Applicable'] ---

                response = self.evaluate_single_aspect(tool_outputs, llm_response, data_type, previous_query, aspect)
                
                if response:
                    input_score, reasonings = convert_scores(response, aspect)

                    # --- Synchronize List Lengths ---
                    if human_score and len(human_score) > 0:
                        target_len = len(human_score)
                    else:
                        # --- Use AI output length or default to 1 ---
                        if isinstance(input_score, list):
                            target_len = len(input_score)
                        else:
                            target_len = 1
                        human_score = ["N/A"] * target_len

                    # --- 1. Normalize Input Scores ---
                    if not isinstance(input_score, list):
                        input_score = [input_score] * target_len
                    
                    # --- Pad/Truncate Input Scores ---
                    input_score = (input_score + ["Error"] * target_len)[:target_len]

                    # --- 2. Normalize Reasonings ---
                    if reasonings is None:
                        reasonings = []
                    if not isinstance(reasonings, list):
                        reasonings = [str(reasonings)]
                    
                    # --- Pad/Truncate Reasonings ---
                    reasonings = (reasonings + [""] * target_len)[:target_len]
                    # -----------------------------------------------

                    new_row = pd.DataFrame({
                        'case': [self.case] * target_len,
                        'aspect': [aspect] * target_len,
                        'human_score': human_score,
                        'input_score': input_score,
                        'reasoning': reasonings
                    })
                    df = pd.concat([df, new_row], ignore_index=True)
                else:
                    # --- Handle API failure ---
                    fallback_len = len(human_score) if human_score else 1
                    fallback_human = human_score if human_score else ["N/A"]
                    
                    df = pd.concat([df, pd.DataFrame({
                        'case': [self.case] * fallback_len,
                        'aspect': [aspect] * fallback_len,
                        'human_score': fallback_human,
                        'input_score': ['Error'] * fallback_len,
                        'reasoning': ['No Response'] * fallback_len
                    })], ignore_index=True)

            # --- Evaluate Correctness (Quantitative) ---
            response = self.evaluate_single_aspect(tool_outputs, llm_response, data_type, previous_query, 'correctness')
            try:
                total_score, _, total_count, _, _ = convert_scores(response, 'correctness')
            except Exception:
                total_score = 0
                total_count = 0

            # --- Store scores in the data dictionary for saving later ---
            data.setdefault("auto_score", {})["total_score"] = total_score
            data.setdefault("auto_score", {})["total_count"] = total_count
            data.setdefault("manual_score", {})["total_score"] = total_score
            data.setdefault("manual_score", {})["total_count"] = total_count

            if data_type == 'literature':
                sbert_score = self.automatic_eval_for_literature(tool_outputs, llm_response)
                data["auto_score"]["sbert_score"] = sbert_score

        # --- Save Results ---
        # --- Save raw data dict ---
        json_path = os.path.join(self.case, 'data_dict.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data_dict, f, indent=4)

        # --- Save CSV report ---
        csv_path = os.path.join(self.case, 'evaluation.csv')
        df.to_csv(csv_path, index=False)
        print(f"Evaluation complete. Results saved to {csv_path}")


    # --- Streamlit Methods (Optional UI) ---
    @staticmethod
    def update_score(i, field):
        """Callback for Streamlit to update scores."""
        data = st.session_state['data_dict'][i]
        data["manual_score"][field] = st.session_state[f"{i}_{field}"]

    def manual_evaluate(self):
        """Runs the Streamlit manual evaluation UI."""
        st.title("Manual Evaluation")

        data_path = os.path.join(self.case, 'data_dict.json')
        if 'data_dict' not in st.session_state:
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    st.session_state['data_dict'] = json.load(f)
            except FileNotFoundError:
                st.error("data_dict.json not found. Run automatic evaluation first.")
                return

        for i, data in enumerate(st.session_state['data_dict']):
            st.markdown(f"---")
            st.markdown(f"**Entry {i+1}**")
            st.markdown(f"**Query**: {data.get('previous_query', 'N/A')}")
            
            with st.expander("Tool Outputs"):
                st.text(data.get('tool_outputs', ''))
            
            with st.expander("LLM Response"):
                st.info(data.get('llm_response', ''))

            # --- Manual inputs ---
            col1, col2 = st.columns(2)
            with col1:
                st.number_input(
                    "Correct Entities", min_value=0, max_value=20, step=1,
                    value=data.get("manual_score", {}).get("total_score", 0),
                    key=f"{i}_total_score",
                    on_change=self.update_score, args=(i, "total_score")
                )
            with col2:
                st.number_input(
                    "Total Entities", min_value=0, max_value=20, step=1,
                    value=data.get("manual_score", {}).get("total_count", 0),
                    key=f"{i}_total_count",
                    on_change=self.update_score, args=(i, "total_count")
                )

        if st.button('Save Manual Scores'):
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(st.session_state['data_dict'], f, indent=4)
            st.success("Saved!")


if __name__ == "__main__":
    print(f"Torch Version: {torch.__version__}")

    # --- 1. Load Config ---
    config_args = {}
    try:
        with open('src/evaluation/config.yaml', 'r') as file:
            config_args = yaml.safe_load(file) or {}
    except FileNotFoundError:
        print('Warning: src/evaluation/config.yaml not found. Using defaults.')

    # --- 2. Parse Command Line Arguments ---
    parser = argparse.ArgumentParser(description='WildfireGPT Evaluation Script')
    parser.add_argument('--model', type=str, default=None, help='LLM model name (overrides config)')
    parser.add_argument('--case_folder', type=str, default=None, help='Path to the case folder')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    cmd_args = parser.parse_args()

    # --- 3. Merge Arguments (CLI > Config > Defaults) ---
    final_args = {
        'llm_model': cmd_args.model or config_args.get('llm_model') or config_model,
        'case_folder': cmd_args.case_folder or config_args.get('case_folder'),
        'verbose': cmd_args.verbose
    }

    # --- 4. Run ---
    if not final_args['case_folder']:
        print("\nError: Case folder is required.")
        print("Usage: python -m src.evaluation.eval_offline --case_folder cases/test_case_1")
    else:
        evaluator = Evaluator(final_args)
        evaluator.llm_evaluate()