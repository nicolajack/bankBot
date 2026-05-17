# Finley - AI-Powered Banking Assistant

An intelligent chatbot assistant for "Bank of Gotham" that helps customers manage their accounts, check balances, view transactions, and get answers to banking policy questions.

## Project Overview

Finley is an AI-powered banking assistant built with cutting-edge technologies to provide a seamless customer experience. The chatbot leverages large language models (LLMs) and retrieval-augmented generation (RAG) to intelligently respond to customer inquiries about their accounts and banking policies.

### Key Features

- **Account Management**: Check balances, view transaction history, and manage multiple accounts
- **Intelligent Q&A**: Ask questions about banking policies, fees, interest rates, and more
- **RAG-Enhanced Responses**: Uses document retrieval to provide accurate policy information
- **Mock Data**: Includes realistic customer, account, and transaction data for testing and demonstration
- **User Authentication**: Simple customer ID-based authentication for account access

## Tech Stack

### Core Technologies
- **Python 3.13**: Primary programming language
- **Streamlit**: Web framework for creating the interactive user interface
- **Ollama**: Local LLM inference engine (uses Llama 3.2 model)
- **LlamaIndex**: Framework for building RAG (Retrieval-Augmented Generation) pipelines
- **ChromaDB**: Vector database for storing and retrieving document embeddings
- **HuggingFace Transformers**: Sentence embeddings via `sentence-transformers/all-MiniLM-L6-v2`

### Supporting Libraries
- **Faker**: Generates mock customer, account, and transaction data
- **JSON**: Data persistence for mock data files

## Architecture

```
┌─────────────┐
│  Streamlit  │ (Web UI)
│    (app)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   Chatbot Module    │ (chatbot.py)
│  ┌───────────────┐  │
│  │  RAG Engine   │  │
│  │  (LlamaIndex) │  │
│  └───────────────┘  │
└──────┬──────────────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
   ┌────────┐          ┌──────────┐
   │ Ollama │          │ ChromaDB │
   │(Llama) │          │(Embedds) │
   └────────┘          └──────────┘
       │
       ▼
   ┌──────────────┐
   │  Mock Data   │
   │  (JSON)      │
   └──────────────┘
```

## Project Structure

```
bankBot/
├── app.py                   # Streamlit web application
├── chatbot.py               # Core chatbot logic and RAG implementation
├── generate_data.py         # Script to generate mock data
├── README.md                # Project documentation
├── mockData/                # Mock database files
│   ├── customers.json       # Customer profiles
│   ├── accounts.json        # Bank accounts
│   └── transactions.json    # Transaction history
├── chroma_db/               # ChromaDB vector store
│   └── [vector embeddings]
└── docs/                    # Documentation and policy files
    ├── faq.md               # Banking FAQs
    ├── feeInfo.md           # Fee information
    ├── savingsAccountPolicy.md # Savings policy
    └── embed.py             # Script to embed documents
```

## Getting Started

### Prerequisites

- Python 3.13+
- Ollama installed and running locally with Llama 3.2 model
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd bankBot
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit ollama llama-index llama-index-vector-stores-chroma llama-index-embeddings-huggingface llama-index-llms-ollama chromadb faker
   ```

4. **Ensure Ollama is running:**
   ```bash
   # In a separate terminal, start Ollama with Llama 3.2
   ollama run llama3.2
   ```

### Setup Steps

1. **Generate mock data (first time only):**
   ```bash
   python generate_data.py
   ```
   This creates:
   - `mockData/customers.json` - 10 sample customers
   - `mockData/accounts.json` - 20 sample accounts
   - `mockData/transactions.json` - 150 sample transactions
    Adjust n1, n2, and n3 variables to tune customer, account, and transaction amounts.

2. **Embed policy documents (first time only):**
   ```bash
   python docs/embed.py
   ```
   This processes the policy documents and stores embeddings in ChromaDB for RAG queries.

## Usage

### Running the Chatbot

Start the Streamlit application:

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

### Using the Chatbot

1. **Authenticate**: Enter a customer ID (0-9) in the sidebar.
2. **Select an Account**: A list of accounts connected to that customer will appear under **Your Accounts** in the sidebar.
   - Click an account to select it.
   - The selected account is highlighted (primary button) and marked with a check (✓).
3. **Ask Questions** in the chat input. All account-specific questions (e.g., balance/transactions) are answered for the **currently selected account**.
   - Examples: "What is the balance of this account?" or "Show my recent transactions."

### Example Interactions

#### Checking Account Balance
```
You: What's my account balance?
Finley: Your Savings account with Account ID 17 has a current balance of $59,279.26. How can I assist you further today?
```

#### Asking About Policies
```
You: What are the overdraft fees?
Finley: According to our policy, overdraft fees are $35 per occurrence. 
        We also offer overdraft protection...
```

#### Viewing Transactions
```
You: Show me my 3 most recent transactions
Finley: Here are your 3 most recent transactions:
        - 05/16/2026: Amazon - $45.99
        - 05/15/2026: Starbucks - $6.50
        - 05/14/2026: Costco - $120.30
```

## Configuration

### Customizing the Chatbot

Edit `chatbot.py` to modify:
- **LLM Model**: Change `MODEL = "llama3.2"` to use a different Ollama model
- **RAG Keywords**: Update `RAG_KEYWORDS` to control which queries trigger document retrieval
- **Embedding Model**: Modify the HuggingFace embedding model in `Settings.embed_model`
- **Similarity K**: Adjust `similarity_top_k=3` for more/fewer retrieved documents

### Adding Policy Documents

1. Add new markdown files to the `docs/` folder
2. Run `python docs/embed.py` to re-embed documents
3. Update `RAG_KEYWORDS` if new topics need to trigger RAG

## Data Files

### customers.json
Contains customer profiles with:
- Name, address, email, phone
- Date of birth, customer ID

### accounts.json
Contains bank accounts with:
- Account type (Checking/Savings)
- Opened date, current balance
- Associated customer ID

### transactions.json
Contains transaction history with:
- Transaction type (deposit, withdrawal, transfer, payment, refund)
- Amount, date, account ID
- Merchant information

## Development Notes

### Account selection + tool context

- The sidebar drives the banking context: users authenticate with a customer ID, then choose one of their connected accounts.
- The chatbot keeps a system prompt that is rewritten on each user message to include the latest `cust_id` and selected `account_id`.
- When the model calls tools, the backend injects `cust_id` automatically and defaults missing `account_id` to the currently selected account.

### Adding New Functionality

1. **New Account Operations**: Add functions to `chatbot.py` following the pattern of `get_balance()` and `get_recent_transactions()`
2. **New Chat Features**: Extend the prompt engineering in `app.py` to guide the LLM's responses
3. **Policy Documents**: Add `.md` files to `docs/` folder and re-run embedding script

### Performance Optimization

- The query engine uses lazy initialization to avoid contacting Ollama at import time
- RAG is only triggered for relevant queries using keyword matching
- Vector store queries are limited to top 3 most similar documents
