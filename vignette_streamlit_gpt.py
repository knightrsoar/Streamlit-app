import autogen
import json
import streamlit as st
import os

def read_vignette(file_path):
    """Helper function to read the vignette file"""
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
            print(f"Successfully read vignette file. Content length: {len(content)} characters")
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Baseline vignette file not found at: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading vignette file: {str(e)}")

# Configuration with hardcoded API key
# Fetch API key from Streamlit secrets
api_key = st.secrets["openai_api_key"]

# Configuration with API key from secrets
config_list = [
    {
        'model': 'gpt-3.5-turbo',
        'api_key': api_key,
        "temperature": 1.0,
 #       "seed": 45735737357357,
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
        "Ensure each agent contributes their expertise, consennsus is reached, and that suggestions are incorporated into the final version."
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
        "Your role is to properly classify the vignette according to the NBME content outline."
        "The NBME content outline is aprt of your knowledge source"
    ),
    llm_config={
        "config_list": config_list,
        "assistant_id": 'asst_PG85C3BIwewAbVuR10iu8Ob6',  # Example Assistant ID for Vignette-Labeler
    },
)

show_off = autogen.AssistantAgent(
    name="Show-Vignette",
    system_message=(
        "Your role is to present the final revised vignette after all improvements have been made. "
        "Format the output exactly as follows:\n"
        "{\n"
        "   'question': ['string'],\n"
        "   'correct_answer': ['string'],\n"
        "   'incorrect_answers': ['string'],\n"
        "   'rationales': ['string'],\n"
        "   'usmle_content_outline': ['string'],\n"
        "}"
    ),
    llm_config=llm_config,
)

# Set up GroupChat
groupchat = autogen.GroupChat(
    agents=[user_proxy, vigmaker, neuro_boss, evaluator, labeler, show_off],
    messages=[],
    max_round=15,
    speaker_selection_method="round_robin",
    allow_repeat_speaker=False,
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config
)

# Streamlit interface
st.title("MultiAgent AI USMLE Vignette Improvement System")

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'process_started' not in st.session_state:
    st.session_state.process_started = False

def start_vignette_process():
    try:
        baseline_vignette = read_vignette("baseline_vignette.txt")
        st.write("Baseline vignette loaded successfully.")
        st.subheader("Baseline Vignette")
        st.write(baseline_vignette)  # Show the baseline vignette at the beginning

        # Create the initial prompt
        prompt = (
            "Let's improve this USMLE STEP 1 clinical vignette. Each agent will contribute their expertise:\n\n"
            "1. Vignette-Maker: Start by reviewing and suggesting improvements\n"
            "2. Neuro-Evaluator: Check neurological and neuroanatomical accuracy\n"
            "3. Evaluator: Assess NBME standards compliance\n"
            "4. Labeler: Classify the content\n"
            "5. Show-Vignette: Present the final improved version\n\n"
            "Here's the vignette to improve:\n\n"
            f"{baseline_vignette}\n\n"
            "Vignette-Maker, please begin by analyzing the vignette and suggesting improvements."
        )

        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Initialize the chat
        result = user_proxy.initiate_chat(
            manager,
            message=prompt,
            silent=True
        )

        # Process and display messages
        for idx, message in enumerate(result.chat_history):
            # Try to get the sender from 'sender', if not present, try 'role', else 'Unknown'
            sender = message.get('sender', message.get('role', 'Unknown'))
            content = message.get('content', '')

            # Add to conversation history
            st.session_state.conversation_history.append((sender, content))
            
            # Update progress
            progress = (idx + 1) / len(result.chat_history)
            progress_bar.progress(progress)
            status_text.text(f"Processing message {idx + 1} of {len(result.chat_history)}")

        # Save results
        with open("conversation.txt", "w", encoding='utf-8') as f:
            json.dump(result.chat_history, f, indent=2)

        # Extract and save final vignette
        final_vignette = None
        for message in reversed(result.chat_history):
            if 'Show-Vignette' in message.get('sender', '') and 'question' in message.get('content', ''):
                final_vignette = message.get('content', '')
                break

        if final_vignette:
            with open("improved_vignette.txt", "w", encoding='utf-8') as f:
                f.write(final_vignette)
            st.success("Process completed! The improved vignette has been saved.")
        else:
            st.warning("Process completed, but no final vignette was found.")

        st.session_state.process_started = True

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Main interface
if not st.session_state.process_started:
    if st.button("Start Vignette Improvement Process"):
        start_vignette_process()

# Display conversation history
if st.session_state.conversation_history:
    st.subheader("Conversation History")
    for sender, content in st.session_state.conversation_history:
        st.markdown(f"**{sender}:**")
        st.write(content)
        st.markdown("---") 
