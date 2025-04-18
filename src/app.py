import streamlit as st
from streamlit_chat import message
import openai
from PIL import Image
from utils.load_config import LoadConfig
from utils.app_utils import Apputils
import json
import traceback

Apputils = Apputils()
APPCFG = LoadConfig()

# Initialize OpenAI client with the API key from LoadConfig
client = openai.OpenAI(api_key=APPCFG.api_key)

# Setting page title and header
im = Image.open("images/chatgpt.png")
st.set_page_config(page_title="Real-time Web Search", page_icon=im, layout="wide")
st.markdown("<h1 style='text-align: center;'>ChatGPT: Real-time Web Search</h1>", unsafe_allow_html=True)

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []

# Sidebar
counter_placeholder = st.sidebar.empty()
st.sidebar.title("ChatGPT")
st.sidebar.image("images/chatgpt.png", use_column_width=True)
model_name = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# Map sidebar model names to OpenAI model names
model_map = {
    "GPT-3.5": "gpt-3.5-turbo",
    "GPT-4": "gpt-4"
}

# Reset everything (Clear button)
if clear_button:
    st.session_state['generated'] = []
    st.session_state['chat_history'] = []
    st.session_state['past'] = []
    st.session_state['model_name'] = []

# Containers
response_container = st.container()
container = st.container()
container.markdown(
    """
    <style>
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            padding: 10px;
            background-color: #f5f5f5;
            border-top: 1px solid #ddd;
        }
    </style>
""", unsafe_allow_html=True)

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You: ", key="input", height=100)
        submit_button = st.form_submit_button(label='Submit')
    
    if user_input:
        chat_history = f"# Chat history:\n{st.session_state['chat_history'][-2:]}\n\n"
        query = f"# User new question:\n {user_input}"
        messages = [
            {"role": "system", "content": str(APPCFG.llm_function_caller_system_role)},
            {"role": "user", "content": chat_history + query}
        ]

        # First LLM Model: to decide which function to call
        first_llm_response = Apputils.ask_llm_function_caller(
            gpt_model=model_map[model_name],
            temperature=APPCFG.temperature,
            messages=messages,
            function_json_list=Apputils.wrap_functions()
        )
        st.session_state['past'].append(user_input)

        if not first_llm_response:
            st.session_state['generated'].append("Error: Failed to get response from LLM. Please try again.")
            chat_history = str(
                (f"User query: {user_input}",
                 "Response: Error: Failed to get response from LLM. Please try again.")
            )
            st.session_state['chat_history'].append(chat_history)
            print("No response from first LLM call")
        else:
            message_dict = first_llm_response.choices[0].message.model_dump()
            print("message_dict:", message_dict)
            if first_llm_response.choices[0].message.tool_calls:
                try:
                    tool_call = first_llm_response.choices[0].message.tool_calls[0]
                    func_name = tool_call.function.name
                    print("called function:", func_name)
                    web_search_result = Apputils.execute_json_function(first_llm_response)
                    if not web_search_result:
                        web_search_results = "\n\n# Web search results:\nNo valid links found. Try searching on platforms like YouTube, LinkedIn Learning, or academic sites."
                    else:
                        # Format results based on function type
                        if func_name == "search_news":
                            formatted_results = "\n".join(
                                [
                                    f"- {r.get('title', 'Untitled')} ({r.get('source', 'Unknown')}): "
                                    f"{r.get('description', 'No description')} [Link: {r.get('url')}]"
                                    for r in web_search_result if r.get('url')
                                ]
                            )
                        elif func_name == "search_video":
                            formatted_results = "\n".join(
                                [
                                    f"- {r.get('title', 'Untitled')} ({r.get('uploader', 'Unknown')}, Duration: {r.get('duration', 'N/A')}): "
                                    f"{r.get('description', 'No description')} [Link: {r.get('url')}]"
                                    for r in web_search_result if r.get('url')
                                ]
                            )
                        elif func_name == "search_pdf":
                            formatted_results = "\n".join(
                                [
                                    f"- {r.get('title', 'Untitled')} ({r.get('source', 'Unknown')}): "
                                    f"{r.get('description', 'No description')} [Link: {r.get('url')}]"
                                    for r in web_search_result if r.get('url')
                                ]
                            )
                        else:
                            formatted_results = "\n".join(
                                [
                                    f"- {r.get('title', 'Untitled')} ({r.get('source', 'Unknown')}): "
                                    f"{r.get('description', 'No description')} [Link: {r.get('url')}]"
                                    for r in web_search_result if r.get('url')
                                ]
                            )
                        web_search_results = f"\n\n# Web search results:\n{formatted_results or 'No valid links found. Try searching on platforms like YouTube, LinkedIn Learning, or academic sites.'}"
                    messages = [
                        {"role": "system", "content": str(APPCFG.llm_system_role)},
                        {"role": "user", "content": chat_history + query + web_search_results}
                    ]
                    print('messages:', messages)
                    # Second LLM Model: to generate the final response
                    second_llm_response = Apputils.ask_llm_chatbot(
                        gpt_model=model_map[model_name],
                        temperature=APPCFG.temperature,
                        messages=messages
                    )
                    if not second_llm_response:
                        raise Exception("Failed to get response from second LLM call")
                    st.session_state['generated'].append(
                        second_llm_response.choices[0].message.content
                    )
                    chat_history = str(
                        (f"User query: {user_input}",
                         f"Response: {second_llm_response.choices[0].message.content}")
                    )
                    st.session_state['chat_history'].append(chat_history)
                except Exception as e:
                    print(f"Error in function call: {str(e)}")
                    traceback.print_exc()
                    messages = [
                        {"role": "system", "content": str(APPCFG.llm_system_role)},
                        {"role": "user", "content": chat_history + query + "\n\n# Web search results:\nNo valid links found. Try searching on platforms like YouTube, LinkedIn Learning, or academic sites."}
                    ]
                    second_llm_response = Apputils.ask_llm_chatbot(
                        gpt_model=model_map[model_name],
                        temperature=APPCFG.temperature,
                        messages=messages
                    )
                    error_message = f"Error in function call: {str(e)}. Falling back to LLM knowledge."
                    if second_llm_response:
                        st.session_state['generated'].append(
                            second_llm_response.choices[0].message.content
                        )
                        chat_history = str(
                            (f"User query: {user_input}",
                             f"Response: {second_llm_response.choices[0].message.content}")
                        )
                    else:
                        st.session_state['generated'].append(error_message)
                        chat_history = str(
                            (f"User query: {user_input}",
                             f"Response: {error_message}")
                        )
                    st.session_state['chat_history'].append(chat_history)
            else:
                try:
                    chat_history = str(
                        (f"User Query: {user_input}",
                         f"Response: {first_llm_response.choices[0].message.content}")
                    )
                    st.session_state['chat_history'].append(chat_history)
                    st.session_state['generated'].append(
                        first_llm_response.choices[0].message.content
                    )
                except Exception as e:
                    print(f"Error in direct response: {str(e)}")
                    st.session_state['generated'].append(
                        "Error: Failed to process direct response. Please try again."
                    )
                    chat_history = str(
                        (f"User query: {user_input}",
                         "Response: Error: Failed to process direct response. Please try again.")
                    )
                    st.session_state['chat_history'].append(chat_history)

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            message(st.session_state['generated'][i], key=str(i))