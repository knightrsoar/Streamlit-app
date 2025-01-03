import autogen
import json
import streamlit as st
import os

def read_vignette(file_path):
    """Helper function to read the vignette file."""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
            print(f"Successfully read vignette file. Content length: {len(content)} characters")
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Baseline vignette file not found at: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading vignette file: {str(e)}")

# Fetch API key from Streamlit secrets
api_key = st.secrets["openai_api_key"]

# Configuration with corrected model name
config_list = [
    {
        'model': 'gpt-4', 
        'api_key': api_key,
        "temperature": 1.0,
    },
]

# LLM configuration
llm_config = {"config_list": config_list, "cache_seed": None, "timeout": 120}

# Define code execution configuration
code_execution_config = {
    "work_dir": "coding",
    "use_docker": False,
    "last_n_messages": 3,
}

# Initialize agents
user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message=(
        "Manager: Coordinate the evaluation and improvement of USMLE STEP 1 clinical vignettes. "
        "Your role is to:\n"
        "1. Start by having the Vignette-Maker review and suggest initial improvements\n"
        "2. Then have the Neuro-Evaluator check neurological accuracy\n"
        "3. Have the Vignette-Evaluator assess NBME standards compliance\n"
        "4. Have the Labeler classify the content\n"
        "5. Finally, have the Show-Vignette present the improved version\n"
        "Ensure each agent contributes their expertise, consensus is reached, and that suggestions are incorporated into the final version."
    ),
    code_execution_config=code_execution_config,
    human_input_mode="NEVER",
)

vigmaker = autogen.AssistantAgent(
    name="Vignette-Maker",
    system_message=(
        "You are responsible for creating and refining clinical vignettes for USMLE STEP 1. "
        "When you receive a vignette:\n"
        "1. Analyze its structure and content\n"
        "2. Suggest specific improvements for clarity and medical accuracy\n"
        "3. Wait for feedback from other experts before making final revisions"
    ),
    llm_config=llm_config,
)

evaluator = autogen.AssistantAgent(
    name="Vignette-Evaluator",
    system_message=(
        "As a NBME standards expert, your role is to:\n"
        "1. Evaluate if the vignette follows NBME style guidelines\n"
        "2. Check if distractors are plausible and educational\n"
        "3. Verify that the question tests appropriate clinical reasoning\n"
        "Provide specific feedback for any violations of NBME standards."
    ),
    llm_config=llm_config,
)

neuro_boss = autogen.AssistantAgent(
    name="Neuro-Evaluator",
    system_message=(
        "As a neurology expert, evaluate:\n"
        "1. Anatomical accuracy of the case\n"
        "2. Correlation between symptoms and proposed lesion locations\n"
        "3. Accuracy of the laterality of the symptoms and lesion location\n"
        "4. Accuracy of neurological exam findings\n"
        "Provide detailed feedback on any neurological inconsistencies."
    ),
    llm_config=llm_config,
)

labeler = autogen.AssistantAgent(
    name="Vignette-Labeler",
    system_message=(
        "Your role is to properly classify the vignette according to the NBME content outline. "
        "The NBME content outline is a part of your knowledge source."
    ),
    llm_config=llm_config,
)

show_off = autogen.AssistantAgent(
    name="Show-Vignette",
    system_message=(
        "Your role is to present the finalized vignette in a clean and concise format for review."
    ),
    llm_config=llm_config,
)

# Implement your logic to call these agents and manage workflow
st.title("Clinical Vignette Manager")
st.write("This app coordinates the improvement of clinical vignettes using multiple specialized agents.")
