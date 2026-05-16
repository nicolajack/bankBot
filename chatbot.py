from ollama import chat
from ollama import ChatResponse
import json
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

import generate_data

MODEL = "llama3.2"

# load data
with open('mockData/accounts.json', 'r') as f:
    ACCOUNTS = json.load(f)
with open('mockData/customers.json', 'r') as f:
    CUSTOMERS = json.load(f)
with open('mockData/transactions.json', 'r') as f:
    TXNS = json.load(f)

# RAG setup
Settings.llm = Ollama(model=MODEL)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("rag_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
query_engine = index.as_query_engine(similarity_top_k=3)

# keywords that suggest the user is asking about bank policy/info docs
RAG_KEYWORDS = {"fee", "policy", "rate", "interest", "overdraft", "faq", "charge", "savings", "penalty", "limit", "rule", "requirement"}

def should_use_rag(text: str) -> bool:
    """Only query ChromaDB if the message looks like a policy/info question."""
    return any(word in text.lower() for word in RAG_KEYWORDS)

def get_rag_context(user_input: str) -> str:
    """Query the RAG pipeline and return retrieved context as a string."""
    result = query_engine.query(user_input)  # synchronous, not aquery
    return str(result).strip()


# tools
def get_balance(account_id: str, cust_id: str):
    account_id = str(account_id)
    account = ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account '{account_id}' not found."}
    if str(account.get("custID")) != str(cust_id):
        return {"error": "Account does not belong to the current customer."}
    return {
        "account_id": account_id,
        "accountType": account.get("accountType"),
        "balance": account.get("balance"),
    }

def get_recent_transactions(account_id: str, cust_id: str, limit: int = 5):
    account_id = str(account_id)
    account = ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account '{account_id}' not found."}
    if str(account.get("custID")) != str(cust_id):
        return {"error": "Account does not belong to the current customer."}

    limit = max(1, min(int(limit) if limit else 5, 20))

    matching = [txn for txn in TXNS.values() if str(txn.get("accountID")) == account_id]
    matching.sort(key=lambda t: (t.get("transactionDate") or ""), reverse=True)
    recent = matching[:limit]

    recent_slim = [
        {
            "transactionDate": t.get("transactionDate"),
            "transactionType": t.get("transactionType"),
            "merchantName": t.get("merchantName"),
            "transactionAmount": t.get("transactionAmount"),
        }
        for t in recent
    ]
    return {
        "account_id": account_id,
        "accountType": account.get("accountType"),
        "recentTransactions": recent_slim,
    }

# tool definitions
get_balance_tool = {
    "type": "function",
    "function": {
        "name": "get_balance",
        "description": "Get the account balance for a given account ID (must belong to the current authenticated customer)",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account ID to get the balance for (e.g. '17')"
                }
            },
            "required": ["account_id"]
        }
    }
}

get_recent_transactions_tool = {
    "type": "function",
    "function": {
        "name": "get_recent_transactions",
        "description": "Get recent transactions for a given account ID (optionally limited)",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account ID to get transactions for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return (default 5, max 20)",
                    "default": 5
                }
            },
            "required": ["account_id"]
        }
    }
}

TOOLS = [get_balance_tool, get_recent_transactions_tool]

TOOLS_REQUIRING_AUTH = {"get_balance", "get_recent_transactions"}

TOOL_FUNCTIONS = {
    "get_balance": get_balance,
    "get_recent_transactions": get_recent_transactions,
}

def dispatch_tool(name, args):
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    return fn(**args)


SYSTEM_PROMPT = """You are an AI assistant that works for "First National Bank." Your name is Finley.
Your purpose is to provide personalized and secure financial assistance to users of the banking application.

Scope: Answer user queries on banking topics such as account management, transactions, and payment schedules.
Provide recommendations for budgeting and savings. Assist users with basic banking issues.

Limits: Do not share sensitive information that could compromise security. Refrain from making decisions
that affect users' financial well-being without their input. Refuse off-topic requests politely.

Communication: Be empathetic, concise, and easy to understand. Never return raw JSON to the user.
If you need information to call a tool, ask the user for it before proceeding."""

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "assistant", "content": "Hello! I'm Finley, your First National Bank assistant. Please enter your customer ID to continue."},
]
print("Finley: Hello! I'm Finley, your First National Bank assistant. Please enter your customer ID to continue.")
print('\nType "quit" to end the chat.\n')

# auth loop
custId = ""
while not custId:
    userInput = input("Enter your customer ID: ").strip()
    if userInput.lower() in ("quit", "exit", ""):
        print("Have a nice day!")
        exit()
    if userInput in CUSTOMERS:
        custId = userInput
        print("Welcome!\n")
    else:
        print("Customer not found, please try again.\n")

# chat loop
while True:
    userInput = input("User: ").strip()
    if userInput.lower() in ("quit", "exit", ""):
        print("Have a nice day!")
        break

    # only hit RAG if the message looks policy/info related
    if should_use_rag(userInput):
        context = get_rag_context(userInput)
        userMsg = f"Context from bank documents:\n{context}\n\nUser question: {userInput}"
    else:
        userMsg = userInput

    messages.append({"role": "user", "content": userMsg})
    response: ChatResponse = chat(model=MODEL, messages=messages, tools=TOOLS)

    if response.message.tool_calls:
        messages.append({
            "role": "assistant",
            "content": response.message.content,
            "tool_calls": response.message.tool_calls,
        })
        for tool_call in response.message.tool_calls:
            name = tool_call.function.name
            args = dict(tool_call.function.arguments or {})
            if name in TOOLS_REQUIRING_AUTH:
                args["cust_id"] = custId
            result = dispatch_tool(name, args)
            messages.append({
                "role": "tool",
                "content": json.dumps(result),
                "name": name,
            })
        response = chat(model=MODEL, messages=messages)

    messages.append({"role": "assistant", "content": response.message.content})
    print("Finley:", response.message.content)