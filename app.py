import json
import streamlit as st
import chatbot

with open('mockData/customers.json', 'r') as f:
    CUSTOMERS = json.load(f)

# page settings (title, icon)
st.set_page_config(
    page_title="Gordon - Bank of Gotham",
    page_icon=":material/account_balance:",
    layout="centered",
    initial_sidebar_state="expanded",
)

# custom styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Montserrat:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], [data-testid="stMarkdownContainer"] {
        font-family: 'Montserrat', sans-serif !important;
        color: #ECEAF4;
    }
            
    h1, h2, h3, h4, h5, h6, .serif {
        font-family: 'Libre Baskerville', serif !important;
    }
            
    .material-symbols-rounded {
        color: #F42937 !important;
        vertical-align: bottom;
        margin-right: 4px;
    }
            
    [data-testid="stSidebar"] > div:first-child {
        background-color: #2A2A36 !important;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid #1A1A1F !important;
    }
            
    .stTextInput input, .stTextArea textarea {
        background-color: #3D3D4E !important;
        border: 1px solid #3D3D4E !important;
        color: #ECEAF4 !important;
        border-radius: 6px !important;
        font-family: 'Montserrat', sans-serif !important;
    }
            
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #3D3D4E !important;
        border: none !important;
        color: #ECEAF4 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #F42937 !important;
        border: none !important;
        color: #ECEAF4 !important;
        border-radius: 8px !important;
    }
            
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
    }

    [data-testid="stChatMessage"]:has(.user-message-marker) {
        background-color: #2A2A36 !important;
        border-radius: 8px !important;
    }

    [data-testid="stChatMessageAvatar"] {
        background-color: #F42937 !important;
        border-radius: 8px !important;
        color: transparent !important;
        width: 32px !important;
        height: 32px !important;
    }

    [data-testid="stChatInput"] {
        background-color: #3D3D4E !important;
        border-radius: 8px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #ECEAF4 !important;
    }
            
    [data-testid="stHeader"] {
        background: transparent !important;
    }
            
    hr {
        border-color: #3D3D4E !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
            
    .bank-header {
        text-align: center;
        font-weight: 700;
        margin-top: -2rem;
        margin-bottom: 0px;
    }
    .bank-subtitle {
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    
    [data-testid="stSidebar"] {
        border-right: 1px solid #1A1A1F !important;
    }

    .bat-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        vertical-align: middle;
        filter: drop-shadow(0 0 4px rgba(244, 41, 55, 0.3)); transform: translateY(0px);
        cursor: pointer;
    }
    .bat-icon svg {
        display: block;
    }

    h1 .bat-icon svg {
        width: 54px;
        height: 48px;
        margin-right: -15px;
        margin-top: -15px;
    }
    h2 .bat-icon svg {
        width: 30px;
        height: 26px;
        margin-top: -5px;
        margin-right: -5px;
    }
</style>
""", unsafe_allow_html=True)

bat_svg = """
<svg fill="#F42937" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 194.328 194.327" xml:space="preserve"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g> <path d="M107.694,6.772c0,0-4.822,16.94-5.429,16.581c-3.148-1.964-8.966-1.778-11.646-0.058 c-0.414-0.947-4.055-16.642-4.055-16.642s-8.717,22.643-6.856,34.793c-0.362,3.547-0.563,11.542,0.186,13.661 c-1.452-1.035-34.132-21.175-33.563-36.084c-31.058,2.563-93.861,123.345,15.326,168.648c-11.85-18.706-19.4-38.533-18.058-48.238 c2.405,1.777,7.176,12.494,20.771,19.303c0-3.989,2.28-22.799,7.812-28.352c2.137,3.166,24.068,51.837,24.068,51.837l24.067-51.837 c0,0,6.46,22.506,4.518,28.059c3.35-2.095,17.78-11.436,21.057-19.01c0.95,2.947,0.943,27.541-16.538,48.238 c28.412-0.037,118.209-102.098,20.666-168.889c-1.93,8.242-31.548,36.139-37.229,36.139c0.061-1.272,0.834-8.607,0-13.476 C113.679,39.441,110.763,19.344,107.694,6.772z"></path> </g> </g></svg>
"""

# header
st.markdown(
    f"""
    <div style="text-align: center; margin-top: 2rem; margin-bottom: 3rem;">
        <h1 class="serif" style="font-size: 3rem; margin-bottom: 0px;"><span class='bat-icon'>{bat_svg}</span> Gordon</h1>
        <p style="color: #ECEAF4; opacity: 0.7; margin-top: 0px;">By Bank of Gotham</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# simple auth: store customer id in session
if "cust_id" not in st.session_state:
    st.session_state.cust_id = ""

if "selected_account" not in st.session_state:
    st.session_state.selected_account = None

# sidebar
with st.sidebar:
    st.markdown(
        f"<h2 class='serif' style='color: #ECEAF4; margin-top: 0;'><span class='bat-icon'>{bat_svg}</span>Bank of Gotham</h2>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("#### :material/lock: Authentication")
    new_id = st.text_input(
        "Enter Customer ID",
        placeholder="e.g., 6",
        help="Enter your unique customer ID to access your account",
        label_visibility="collapsed",
        value=st.session_state.cust_id,
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
                <div style="padding: 15px; border-radius: 8px; background-color: #3D3D4E; border: 1px solid #1A1A1F; text-align: center; margin: 1rem 0;">
                    <p style="margin: 0; color: #ECEAF4; font-size: 0.9rem;">Welcome Back,</p>
                    <p class="serif" style="margin: 0; color: #C00014; font-size: 1.4rem; font-weight: 700;">{cust.get('name')}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

            st.markdown('#### :material/credit_card: Your Accounts')
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
    st.markdown("#### :material/menu_book: About Gordon")
    st.markdown(
        """
        <div style="background-color: #3D3D4E; padding: 15px; border-radius: 8px;">
            Gordon is an AI-powered banking assistant that helps you manage your accounts, 
            check transaction history, and answer questions about our banking policies.
        </div>
        """, 
        unsafe_allow_html=True
    )
    # clear chat/start new convo (may need to edit look)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear Chat", type="primary"):
        if hasattr(chatbot, 'new_conversation'):
            st.session_state.messages = chatbot.new_conversation()
        else:
            st.session_state.messages = []
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
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
        if message["role"] == "user":
            st.markdown(f'<span class="user-message-marker" style="display: none;"></span>{message["content"]}', unsafe_allow_html=True)
        else:
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
            st.markdown(f'<span class="user-message-marker" style="display: none;"></span>{prompt}', unsafe_allow_html=True)

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