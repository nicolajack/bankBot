import json
import streamlit as st
import chatbot

with open('mockData/customers.json', 'r') as f:
    CUSTOMERS = json.load(f)

# page settings (title, icon)
st.set_page_config(
    page_title="Gordon - Bank of Gotham",
    page_icon=":material/savings:",
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
st.markdown('<h1 class="bank-header">🏦 Gordon</h1>', unsafe_allow_html=True)
st.markdown('<p class="bank-subtitle">Your Bank of Gotham AI Assistant</p>', unsafe_allow_html=True)

# simple auth: store customer id in session
if "cust_id" not in st.session_state:
    st.session_state.cust_id = ""

if "selected_account" not in st.session_state:
    st.session_state.selected_account = None

# sidebar
with st.sidebar:
    st.markdown("### 🏦 Bank of Gotham")
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
        cust = CUSTOMERS.get(st.session_state.cust_id)
        if cust:
            # show customers name w/ profile card style
            st.markdown(
                f"""
                <div style="padding: 15px; border-radius: 8px; background-color: #f1f5f9; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 1rem;">
                    <p style="margin: 0; color: #64748b; font-size: 0.9rem;">Welcome back,</p>
                    <p style="margin: 0; color: #1e40af; font-size: 1.2rem; font-weight: 700;">{cust.get('name')}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

            st.markdown('#### 💳 Your Accounts')
            accounts = chatbot.get_customer_accounts(cust_id=st.session_state.cust_id)
            if accounts:
                for acc in accounts:
                    acc_id = acc["account_id"]
                    acc_type = acc["accountType"]
                    
                    is_selected = st.session_state.selected_account == acc_id
                    button_label = f"{'✓ ' if is_selected else ''}{acc_type} Account #{acc_id}"
                    button_style = "primary" if is_selected else "secondary"

                    if st.button(
                        button_label,
                        key=f"account_{acc_id}",
                        use_container_width=True,
                        type=button_style
                    ):
                        st.session_state.selected_account = acc_id
                        st.rerun()
            else:
                st.warning("No accounts found for this customer.")
        else:
            st.error("❌ Customer ID not found.")
    else:
        st.warning("Please enter your ID to begin.")

    st.markdown("---")
    st.markdown("#### 📚 About Gordon")
    st.info(
        "Gordon is an AI-powered banking assistant that helps you manage your accounts, "
        "check transaction history, and answer questions about our banking policies."
    )
    # clear chat/start new convo (may need to edit look)
    if st.button("Clear Chat"):
        st.session_state.messages = chatbot.new_conversation()
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>"
        "© 2026 Bank of Gotham<br>Secure Session</p>",
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
    avatar_icon = ":material/sentiment_excited:" if message["role"] == "user" else ":material/account_balance:"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# react to user input
if prompt := st.chat_input("Ask Gordon a question (e.g., 'What is my balance?')..."):
    # if not authenticated, guide the user
    if not st.session_state.cust_id.strip():
        with st.chat_message("assistant", avatar=":material/account_balance:"):
            st.warning("⚠️ Please enter your Customer ID in the secure sidebar menu to continue.")
    elif not st.session_state.selected_account:
        with st.chat_message("assistant", avatar=":material/account_balance:"):
            st.warning("⚠️ Please select an account in the secure sidebar menu to continue.")
    else:
        # display user message immediately
        with st.chat_message("user", avatar=":material/sentiment_excited:"):
            st.markdown(prompt)

        # get response with spinner
        with st.chat_message("assistant", avatar=":material/account_balance:"):
            with st.spinner("Gordon is checking..."):
                reply, st.session_state.messages = chatbot.respond(
                    st.session_state.messages,
                    prompt,
                    cust_id=st.session_state.cust_id.strip(),
                    account_id=st.session_state.selected_account,
                )
            
        # force re-render to show chat history including new response
        st.rerun()