from src.evaluation.utils import *

class Prompts:
    def __init__(self):
        pass

    def evaluate_relevance_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        """
        STRICTER VERSION: Removed 'Don't be too harsh' and added critical instructions.
        """
        message = [
            "You are a strict QA Auditor. Your task is to critically analyze the relevance of the model's response. "
            "For each question, answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. "
            "If the response is vague, generic, or slightly off-topic, mark it as 'Could be better' or 'No'. "
            "Do not give the model the benefit of the doubt. "
            "Output strictly a Python list like ['Yes', 'No', 'Not Applicable']. Do NOT provide any preamble or explanation before the list.",

            "Given this model's response: \n" + llm_response + "\n\n"
            "(1) Does the response DIRECTLY answer the user's last question? The question is '" + str(previous_query) + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
            "(2) Is the response specifically tailored to the user's profession? The profession is '" + str(user_profile.get('profession', 'Unknown')) + "' Answer 'Yes' only if specific professional context is used, otherwise 'Could be better' or 'No'.\n"
            "(3) Is the response directly addressing the user's concern? The concern is '" + str(user_profile.get('concern', 'Unknown')) + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
            "(4) Is the response accurate to the user's location? The location is '" + str(user_profile.get('location', 'Unknown')) + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
            "(5) Is the response strictly adhering to the user's timeline? The timeline is '" + str(user_profile.get('timeline', 'Unknown')) + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
            "Please answer these questions one by one with your reasoning. You MUST mark the response to each question in a format of (1), (2), (3), (4), and (5).\n"
            "Lastly, output a Python list of your responses."
        ]
        return message

    def evaluate_relevance_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        return self.evaluate_relevance_in_reference(tool_output, llm_response, user_profile, previous_query)

    def evaluate_entailment_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        """
        STRICTER VERSION: Checks for hallucinations.
        """
        message = [
            "You are a Fact-Checker. Your task is to verify if the model's response is supported by the Tool Outputs. "
            "If the model claims something not present in the tool outputs, it is a Hallucination. "
            "Output strictly a Python list like ['Yes', 'No', 'Not Applicable']. Do NOT provide any preamble or explanation before the list.",

            "Tool Outputs (Facts): \n" + str(tool_output) + "\n\n"
            "Model Response: \n" + llm_response + "\n\n"
            "(1) Does the response contain information that contradicts the Tool Outputs? Answer 'Yes' (Bad), 'No' (Good), or 'Not Applicable'.\n"
            "(2) Does the response hallucinate new facts not found in the Tool Outputs? Answer 'Yes' (Bad), 'No' (Good), or 'Not Applicable'.\n"
            "(3) Is the response fully supported by the provided context? Answer 'Yes' (Good), 'No' (Bad), or 'Not Applicable'.\n"
            "Please answer these questions one by one with your reasoning. You MUST mark the response to each question in a format of (1), (2), and (3).\n"
            "Lastly, output a Python list of your responses."
        ]
        return message

    def evaluate_entailment_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        return self.evaluate_entailment_in_reference(tool_output, llm_response, user_profile, previous_query)

    def evaluate_accessibility_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = [
            "You are a ruthless Editor. Your goal is to keep responses short and concise.",
            "Analyze the model's response length and fluff.",
            "Output strictly a Python list like ['Yes', 'No']. Do NOT provide any preamble or explanation before the list.",
            "Given this model's response: \n" + llm_response + "\n",
            
            "(1) Is the response concise? Answer 'No' if it contains unnecessary compliments like 'That's a great location!' or 'That's a valid concern!'. Answer 'Yes' only if it gets straight to the point.\n",
            "(2) Does it use fewer than 50 words? Answer 'Yes' or 'No'.\n",
            "(3) Is the tone professional? Answer 'Yes', 'No', or 'Could be better'.\n",
            
            "Output a Python list of your responses."
        ]
        return message

    def evaluate_accessibility_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        return self.evaluate_accessibility_in_reference(tool_output, llm_response, user_profile, previous_query)

    def evaluate_correctness_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        """
        Standard Correctness check.
        """
        message = [
            "You are a strict grader. Compare the model's response to the tool outputs. "
            "Identify key entities (locations, numbers, dates, specific names) in the Tool Outputs and check if they appear correctly in the Response.\n",

            "Tool Outputs: \n" + str(tool_output) + "\n\n"
            "Model Response: \n" + llm_response + "\n\n"
            "Step 1: List specific entities found in Tool Outputs.\n"
            "Step 2: Check if they are preserved in the Model Response.\n"
            "Output the final score as a fraction: [Matches]/[Total Entities].\n"
            "Example Output: 'The response correctly identifies 3 out of 4 entities. Score: 3/4'"
        ]
        return message

    def evaluate_correctness_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        return self.evaluate_correctness_in_reference(tool_output, llm_response, user_profile, previous_query)