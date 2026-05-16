import streamlit as st
import chatbot

# streamlit frontend

st.title("Finley - Your First National Bank Assistant")

# simple auth: store customer id in session
if "cust_id" not in st.session_state:
    st.session_state.cust_id = ""

with st.sidebar:
    new_id = st.text_input("Customer ID")
    if new_id != st.session_state.cust_id:
        st.session_state.cust_id = new_id
        st.session_state.messages = chatbot.new_conversation()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = chatbot.new_conversation()

DISPLAY_ROLES = {"user", "assistant"}

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] not in DISPLAY_ROLES:
        continue
    if message["role"] == "assistant" and not message.get("content"):
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask Finley a question"):
    # If not authenticated, guide the user
    if not st.session_state.cust_id.strip():
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            st.markdown("Please enter your Customer ID in the sidebar to continue.")
    else:
        with st.chat_message("user"):
            st.markdown(prompt)

        reply, st.session_state.messages = chatbot.respond(
            st.session_state.messages,
            prompt,
            cust_id=st.session_state.cust_id.strip(),
        )

        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            st.markdown(reply)