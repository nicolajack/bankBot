import streamlit as st
import chatbot

# page settings (title, icon)
st.set_page_config(
    page_title="Finley - First National Bank",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="expanded",
)

# custom styles
st.markdown("""
<style>
    .bank-header {
        text-align: center;
        color: #1e40af;
        font-weight: 700;
        margin-top: -2rem;
        margin-bottom: 0px;
    }
    .bank-subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    /* Adds a subtle dividing line to the sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# header
st.markdown('<h1 class="bank-header">🏦 Finley</h1>', unsafe_allow_html=True)
st.markdown('<p class="bank-subtitle">Your First National Bank AI Assistant</p>', unsafe_allow_html=True)

# simple auth: store customer id in session
if "cust_id" not in st.session_state:
    st.session_state.cust_id = ""

# sidebar
with st.sidebar:
    st.markdown("### 🏦 First National Bank")
    st.markdown("---")
    st.markdown("#### 🔐 Authentication")
    new_id = st.text_input(
        "Enter Customer ID",
        placeholder="e.g., 6",
        help="Enter your unique customer ID to access your account",
        label_visibility="collapsed"
    )
    if new_id != st.session_state.cust_id:
        st.session_state.cust_id = new_id
        st.session_state.messages = chatbot.new_conversation()
    
    if st.session_state.cust_id:
        st.success(f"✓ Logged in as: **{st.session_state.cust_id}**")
    else:
        st.warning("Please enter your ID to begin.")
    
    st.markdown("---")
    st.markdown("#### 📚 About Finley")
    st.info(
        "Finley is an AI-powered banking assistant that helps you manage your accounts, "
        "check transaction history, and answer questions about our banking policies."
    )
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>"
        "© 2026 First National Bank<br>Secure Session</p>",
        unsafe_allow_html=True
    )

# init chat history
if "messages" not in st.session_state:
    st.session_state.messages = chatbot.new_conversation()

DISPLAY_ROLES = {"user", "assistant"}

# display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] not in DISPLAY_ROLES:
        continue
    if message["role"] == "assistant" and not message.get("content"):
        continue
        
    # assign avatar based on role
    avatar_icon = "🧑" if message["role"] == "user" else "🏦"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# react to user input
if prompt := st.chat_input("Ask Finley a question (e.g., 'What is my balance?')..."):
    # if not authenticated, guide the user
    if not st.session_state.cust_id.strip():
        with st.chat_message("assistant", avatar="🏦"):
            st.warning("⚠️ Please enter your Customer ID in the secure sidebar menu to continue.")
    else:
        # display user message immediately
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # get response with spinner
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Finley is checking..."):
                reply, st.session_state.messages = chatbot.respond(
                    st.session_state.messages,
                    prompt,
                    cust_id=st.session_state.cust_id.strip(),
                )
            
        # gorce re-render to show chat history including new response
        st.rerun()