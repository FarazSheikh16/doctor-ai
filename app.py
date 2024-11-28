import streamlit as st
import requests
from src.utils import load_config
from src.constants import CONFIG_PATH


config = load_config(CONFIG_PATH)
api_config = config['api']

# Set up Streamlit page
st.set_page_config(page_title="Medical Chatbot", page_icon="🤖", layout="centered")
st.title("Medical Chatbot 🤖")
st.write("Ask me anything about medical information, and I'll provide a response based on our knowledge base.")

# Chat history storage
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# User input area
with st.form(key="chat_form", clear_on_submit=True):
    user_query = st.text_input("Enter your question:")
    submit_button = st.form_submit_button("Submit")

# When the user submits a query
if submit_button and user_query.strip():
    # Append user query to chat history
    st.session_state.chat_history.append({"role": "user", "message": user_query})

    # Send the query to the FastAPI backend
    try:
        response = requests.post(api_config['generate_url'], json={"query": user_query, "num_results": 5})
        if response.status_code == 200:
            api_response = response.json()
            bot_response = api_response.get("response", "Sorry, I couldn't generate a response.")
            sources = api_response.get("sources", [])
        else:
            bot_response = f"Error: {response.json().get('detail', 'Something went wrong.')}"
            sources = []
    except Exception as e:
        bot_response = f"Error: {str(e)}"
        sources = []

    # Append bot response and sources to chat history
    st.session_state.chat_history.append({"role": "bot", "message": bot_response, "sources": sources})

# Display chat history
st.divider()  # Adds a visual divider between the chat input and history
st.header("Chat History")
for entry in st.session_state.chat_history:
    if entry["role"] == "user":
        st.markdown(f"**You:** {entry['message']}")
    elif entry["role"] == "bot":
        st.markdown(f"**Bot:** {entry['message']}")
        if entry.get("sources"):
            st.markdown("**Sources:**")
            for source in entry["sources"]:
                st.markdown(f"- {source}")

# Provide feedback or clear option
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("Clear Chat"):
        st.session_state.chat_history = []

with col2:
    st.write("Feedback? Let us know!")

# Add "Ingest Data" button
if st.button("Ingest Data"):
    try:
        # Call the FastAPI ingest endpoint
        ingest_response = requests.post(api_config['ingest_url'])
        if ingest_response.status_code == 200:
            st.success("Data ingested successfully!")
        else:
            st.error(f"Failed to ingest data: {ingest_response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error during ingestion: {str(e)}")
