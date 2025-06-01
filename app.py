import streamlit as st
import requests
import json
import base64
import re
from streamlit_star_rating import st_star_rating

# Page configuration
st.set_page_config(
    page_title="Alexander The Cook",
    layout="centered"
)


st.markdown(
        f"""
        <style>
        .stApp {{
            background-size: cover;
            background-color: #fdf0d5;
            color: #333333;
        }}
        
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@100..900&family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap');
        
        html, body, [class*="css"] {{
            font-family: Lexend, sans-serif;
        }}
        
        .stMarkdown {{
            color: #333333;
        }}
        
        .stButton button {{
            background-color: #FF6B6B;
            color: white;
            font-family: Montserrat, sans-serif;
        }}
        
        .stTextInput input {{
            font-family: Montserrat, sans-serif;
        }}
        
        /* Center the chat container */
        .main .block-container {{
            max-width: 700px;
            padding-top: 0;
            padding-bottom: 0;
            margin: 0 auto;
        }}
        
        /* Style for the chat messages */
        .stChatMessage {{
            background-color: #F8F8F8;
            border-radius: 10px;
            margin-bottom: 10px;
            padding: 10px;
        }}
        
        </style>
        """,
        unsafe_allow_html=True
    )

# Bold headers
st.markdown("**Alexander the cook**")
st.markdown("**Hi I'm Alexander the cook, I'm here to help you make delicious recipes! Let's cook!**")

# Create some vertical space to push content to the middle
st.markdown("<div style='height: 10vh'></div>", unsafe_allow_html=True)

# Initialize chat history and selections
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_diet" not in st.session_state:
    st.session_state.selected_diet = "None"
if "selected_ingredients" not in st.session_state:
    st.session_state.selected_ingredients = []
if "other_requirements" not in st.session_state:
    st.session_state.other_requirements = ""
if "rating" not in st.session_state:
    st.session_state.rating = 3  # Default to 3 stars

# Dietary requirements
st.markdown("### Dietary Requirements")
dietary_options = [
    "None", "Vegan", "Vegetarian", "Kosher", "Halal", "Gluten-Free", "Dairy-Free"
]
selected_diet = st.selectbox(
    "Choose a dietary requirement (optional):",
    dietary_options,
    index=dietary_options.index(st.session_state.selected_diet)
)
st.session_state.selected_diet = selected_diet

# Common ingredients
st.markdown("### Common Ingredients")
common_ingredients = [
    "Eggs", "Milk", "Flour", "Sugar", "Butter", "Chicken", "Rice",
    "Tomato", "Cheese", "Potato", "Onion", "Garlic", "Spinach"
]
selected_ingredients = st.multiselect(
    "Select common ingredients you have (optional):",
    common_ingredients,
    default=st.session_state.selected_ingredients
)
st.session_state.selected_ingredients = selected_ingredients

# Other requirements
other_requirements = st.text_input(
    "Other requirements (optional):",
    value=st.session_state.other_requirements,
    placeholder="e.g. nut-free, no mushrooms, quick to make"
)
st.session_state.other_requirements = other_requirements

# Star rating for cooking skill
st.markdown("### Rate your cooking skill")
st_star_rating(
    label="How would you rate your cooking skill? (1 = Beginner, 5 = Expert)",
    maxValue=5,
    defaultValue=st.session_state.rating,
    key="rating"
)
# Do NOT assign to st.session_state.rating after widget creation!

col1, col2 = st.columns([2, 1])
with col1:
    generate = st.button("🍳 Generate Recipe", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear", type="secondary", use_container_width=True)

# Display chat history in a container to center it
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if generate:
    # Build the full prompt
    prompt_parts = []
    if selected_diet != "None":
        prompt_parts.append(f"Dietary requirement: {selected_diet}")
    if selected_ingredients:
        prompt_parts.append(f"Ingredients: {', '.join(selected_ingredients)}")
    if other_requirements:
        prompt_parts.append(f"Other requirements: {other_requirements}")
    prompt_parts.append(f"User cooking skill rating: {st.session_state.rating}/5")
    prompt_parts.append(
        "Please generate a clear, step-by-step recipe that strictly follows the selected dietary requirement and uses the chosen ingredients as much as possible. "
        "Include cooking instructions, preparation time, and difficulty level. Do not use LaTeX or /boxed formatting in your response."
    )
    full_prompt = " | ".join(prompt_parts) 

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": full_prompt})

    # Display user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(full_prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            # Call the API
            with st.spinner("Finding recipes..."):
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer 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",
                        "Content-Type": "application/json",
                    },
                    data=json.dumps({
                        "model": "deepseek/deepseek-r1-zero:free",
                        "messages": [
                            {"role": "system", 
                             "content": "You are a cooking assistant specialized in creating recipes from available ingredients. Suggest one delicious recipe based on the ingredients the user provides. Include cooking instructions, preparation time, and difficulty level when possible. If question that are unrelated to cooking, please redirect user to ask a cooking related question as you are a cooking assistant only."},
                            *st.session_state.messages
                        ],
                    })
                )

                if response.status_code == 200:
                    assistant_response = response.json()["choices"][0]["message"]["content"]
                    # Remove any /boxed{...} or similar LaTeX artifacts
                    assistant_response = re.sub(r"/boxed\{.*?\}", "", assistant_response)
                    message_placeholder.markdown(assistant_response)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                else:
                    message_placeholder.error(f"Error: {response.status_code}. Please try again.")

if clear:
    st.session_state.messages = []
    st.session_state.selected_diet = "None"
    st.session_state.selected_ingredients = []
    st.session_state.other_requirements = ""
    st.rerun(scope="app")  # For Streamlit >=1.37

# Add styling with Africa Trial font and light theme
st.markdown(f"""
<style>
    
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: Montserrat, sans-serif;
    }}
    
    .stApp {{
        background-color: #FFFFFF;
        color: #333333;
    }}
    
    .stMarkdown {{
        color: #333333;
    }}
    
    .stButton button {{
        background-color: #FF6B6B;
        color: white;
        font-family: Montserrat, sans-serif;
    }}
    .stButton button:nth-child(2) {{
        background-color: #CCCCCC;
        color: #333;
        margin-left: 1em;
    }}
    
    .stTextInput input {{
        font-family: Montserrat, sans-serif;
    }}
    
    /* Center the chat container */
    .main .block-container {{
        max-width: 700px;
        padding-top: 0;
        padding-bottom: 0;
        margin: 0 auto;
    }}
    
    /* Style for the chat messages */
    .stChatMessage {{
        background-color: #F8F8F8;
        border-radius: 10px;
        margin-bottom: 10px;
        padding: 10px;
    }}
</style>
""", unsafe_allow_html=True)


# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat container
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input and processing user prompt
if prompt := st.chat_input("Enter ingredients you have..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty() 

        with st.spinner("Creating recipe..."):
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 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",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "deepseek/deepseek-r1-zero:free",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a chatbot to help the user cook. When the user gives you certain ingredients "
                                "and/or dietary requirements, generate a delicious recipe and tell them the instructions "
                                "in bullet points, time required to make the dish, and difficulty. If the user asks anything "
                                "unrelated to cooking or food, do not answer and redirect them to ask questions about cooking only. "
                                "Answer simply in bullet points."
                            )
                        },
                        *st.session_state.messages
                    ],
                }) 
            )

            if response.status_code == 200:
                assistant_response = response.json()["choices"][0]["message"]["content"]
                message_placeholder.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            else:
                message_placeholder.error(f"Error: {response.status_code}. Please try again.")
