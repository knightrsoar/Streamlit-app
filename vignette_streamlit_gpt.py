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
llm_config = {"config_list": config_list, "cache_seed": None, "timeout": 1200}

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
        "Ensure each agent contributes their expertise, consensus is reached, and suggestions are incorporated into the final version."
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
        "3. Wait for feedback from other experts before making final revisions."
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

evaluator = autogen.AssistantAgent(
    name="Vignette-Evaluator",
    system_message=(
        "As an NBME standards expert, your role is to:\n"
        "1. Evaluate if the vignette follows NBME style guidelines\n"
        "2. Check if distractors are plausible and educational\n"
        "3. Verify that the question tests appropriate clinical reasoning\n"
        "Provide specific feedback for any violations of NBME standards."
    ),
    llm_config=llm_config,
)

labeler = autogen.AssistantAgent(
    name="Vignette-Labeler",
    system_message=(
        "Your role is to properly classify the vignette according to the NBME content outline."
        "The NBME content outline is part of your knowledge source."
    ),
    llm_config=llm_config,
)

# Streamlit app
st.title("USMLE STEP 1 Vignette Improvement System")

if st.button("Start Vignette Process"):
    try:
        # Step 1: Initial vignette (can be replaced with file input or user input)
        initial_vignette = {
            "question": "A 45-year-old man presents to the clinic with a 6-month history of progressive numbness and tingling in his left arm and leg. He also reports occasional episodes of sharp, shooting pain in the same areas. His medical history is significant for poorly controlled diabetes mellitus. Physical examination reveals decreased sensation to pinprick and temperature in the left arm and leg, with preserved vibration and proprioception. Which of the following locations is most likely the site of the lesion causing these symptoms?",
            "correct_answer": "Left lateral spinothalamic tract",
            "incorrect_answers": [
                "Right lateral spinothalamic tract",
                "Left dorsal columns",
                "Right dorsal columns",
                "Left corticospinal tract",
            ],
            "rationales": [
                "The correct answer is the left lateral spinothalamic tract. This tract carries pain and temperature sensations. The patient's symptoms of decreased sensation to pinprick and temperature, along with the unilateral distribution, suggest a lesion in the spinothalamic tract on the same side as the symptoms.",
                "The right lateral spinothalamic tract is incorrect because it carries sensations from the opposite side of the body. A lesion here would cause symptoms in the right arm and leg, not the left.",
                "The left dorsal columns are incorrect because they primarily carry vibration and proprioceptive sensations. A lesion in this area would affect these modalities, which are preserved in this patient.",
                "The right dorsal columns are also incorrect for the same reason as the left dorsal columns. Additionally, a lesion here would affect the right side of the body.",
                "The left corticospinal tract is incorrect because it primarily carries motor fibers, not sensory. A lesion in this tract would typically present with weakness or paralysis, not sensory deficits.",
            ],
        }

        # Step 1: Vignette-Maker
        maker_output = vigmaker.process(initial_vignette)
        if not maker_output:
            raise ValueError("Vignette-Maker did not produce an output.")

        # Step 2: Neuro-Evaluator
        neuro_output = neuro_boss.process(maker_output)
        if not neuro_output:
            raise ValueError("Neuro-Evaluator did not produce an output.")

        # Step 3: Evaluator
        eval_output = evaluator.process(neuro_output)
        if not eval_output:
            raise ValueError("Evaluator did not produce an output.")

        # Step 4: Labeler
        label_output = labeler.process(eval_output)
        if not label_output:
            raise ValueError("Labeler did not produce an output.")

        # Step 5: Show-Vignette
        st.success("Final Improved Vignette:")
        st.json(label_output)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
