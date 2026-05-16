from pathlib import Path
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

# RAG setup (lazy-init query engine to avoid contacting Ollama at import time)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
BASE_DIR = Path(__file__).parent
chroma_client = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))
chroma_collection = chroma_client.get_or_create_collection("rag_collection")
print(chroma_collection.count())
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
_query_engine = None


def get_query_engine():
    global _query_engine
    if _query_engine is None:
        # LLM is only required for response synthesis; set it when we actually need RAG
        Settings.llm = Ollama(model=MODEL)
        _query_engine = index.as_query_engine(similarity_top_k=3)
    return _query_engine

# keywords that suggest the user is asking about bank policy/info docs
RAG_KEYWORDS = {"fee", "policy", "rate", "interest", "overdraft", "faq", "charge", "savings", "penalty", "limit", "rule", "requirement"}

def should_use_rag(text: str) -> bool:
    """Only query ChromaDB if the message looks like a policy/info question."""
    return any(word in text.lower() for word in RAG_KEYWORDS)

def get_rag_context(user_input: str) -> str:
    """Query the RAG pipeline and return retrieved context as a string."""
    try:
        qe = get_query_engine()
        result = qe.query(user_input)  # synchronous, not aquery
        return str(result).strip()
    except ConnectionError:
        # Ollama not reachable; fall back to no-context
        return ""
    except Exception:
        return ""


# tools
def get_balance(account_id: str, cust_id: str, **kwargs):
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

def get_recent_transactions(account_id: str, cust_id: str, limit: int = 5, **kwargs):
    account_id = str(account_id)
    account = ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account '{account_id}' not found."}
    if str(account.get("custID")) != str(cust_id):
        return {"error": "Account does not belong to the current customer."}

    limit = _normalize_limit(limit)

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

def get_customer_info(cust_id: str, **kwargs):
    cust = CUSTOMERS.get(cust_id)
    if not cust :
        return {"error: Customer not found."}
    if str(cust.get("custID")) != str(cust_id):
        return {"error": "Customer is not properly logged in."}

    # also include the user's accounts so the LLM knows their account IDs
    user_accounts = [
        {"account_id": acc_id, "accountType": acc_data.get("accountType")}
        for acc_id, acc_data in ACCOUNTS.items()
        if str(acc_data.get("custID")) == str(cust_id)
    ]

    return {
        "cust_id": cust_id,
        "name": cust.get("name"),
        "address": cust.get("address"),
        "phone": cust.get("phone"),
        "email": cust.get("email"),
        "dob": cust.get("dob"),
        "accounts": user_accounts,
    }

def _normalize_limit(limit, default=5, max_limit=20):
    if limit is None:
        return default
    if isinstance(limit, str) and limit.strip().lower() in {"", "null", "none", "nil"}:
        return default
    try:
        return max(1, min(int(limit), max_limit))
    except (ValueError, TypeError):
        return default

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

get_customer_info_tool = {
    "type": "function",
    "function": {
        "name": "get_customer_info",
        "description": "Get customer information for the currently authenticated customer.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

TOOLS = [get_balance_tool, get_recent_transactions_tool, get_customer_info_tool]

TOOLS_REQUIRING_AUTH = {"get_balance", "get_recent_transactions", "get_customer_info"}

TOOL_FUNCTIONS = {
    "get_balance": get_balance,
    "get_recent_transactions": get_recent_transactions,
    "get_customer_info": get_customer_info,
}

def dispatch_tool(name, args):
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    
    # filter out any invalid parameter names the LLM might hallucinate (like '[]')
    clean_args = {k: v for k, v in args.items() if isinstance(k, str) and k.isidentifier()}
    
    try:
        return fn(**clean_args)
    except Exception as e:
        return {"error": f"Failed to execute {name}: {str(e)}"}

SYSTEM_PROMPT = """You are an AI assistant that works for "First National Bank." Your name is Finley.
Your purpose is to provide personalized and secure financial assistance to users of the banking application.

Scope: Answer user queries on banking topics such as account management, transactions, and payment schedules.
Provide recommendations for budgeting and savings. Assist users with basic banking issues.

Limits: Do not share sensitive information that could compromise security. Refrain from making decisions
that affect users' financial well-being without their input. Refuse off-topic requests politely.
If the user asks for account details but you do not have access to their customer ID via your tools, politely ask them to authenticate using the sidebar.

Communication: Be empathetic, concise, and easy to understand. Never return raw JSON to the user. Do not wrap your response in markdown code blocks (e.g. ```).
If you need information to call a tool, ask the user for it before proceeding.

Tools and Context: You have access to exactly THREE tools: get_balance, get_recent_transactions, and get_customer_info. 
NEVER hallucinate or invent new tools. If you cannot answer a question using these three tools, or if the question is about policies, fees, FAQs, or general bank information, simply provide a direct text response using your general knowledge and any context text already provided in the user's message. DO NOT try to call a tool for this (e.g., do not call 'get_context_from_bank_documents' or 'get_fees').

Formatting: When displaying transaction history, always format the data as a clean Markdown table. Never display pure JSON to the user."""


def new_conversation() -> list[dict]:
    """Create a fresh messages list suitable for Ollama chat."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hello! I'm Finley, your First National Bank assistant. Enter your Customer ID in the sidebar to get started."},
    ]


def respond(messages: list[dict], user_input: str, *, cust_id: str | None = None) -> tuple[str, list[dict]]:
    """Handle one user turn and return (assistant_text, updated_messages)."""
    user_input = (user_input or "").strip()

    # add optional retrieved context
    if should_use_rag(user_input):
        context = get_rag_context(user_input)
        if context:
            messages.append({
                "role": "system", 
                "content": f"Context from bank documents to help answer the user's next question:\n{context}"
            })

    messages.append({"role": "user", "content": user_input})

    try:
        response: ChatResponse = chat(model=MODEL, messages=messages, tools=TOOLS)
    except ConnectionError:
        assistant_text = "I can't reach the local Ollama server right now. Please make sure Ollama is installed and running, then try again."
        messages.append({"role": "assistant", "content": assistant_text})
        return assistant_text, messages

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
                if not cust_id:
                    tool_result = {"error": "Missing customer ID. Please authenticate first."}
                else:
                    args["cust_id"] = cust_id
                    tool_result = dispatch_tool(name, args)
            else:
                tool_result = dispatch_tool(name, args)

            messages.append({
                "role": "tool",
                "content": json.dumps(tool_result),
                "name": name,
            })

        try:
            response = chat(model=MODEL, messages=messages)
        except ConnectionError:
            assistant_text = "I can't reach the local Ollama server right now. Please make sure Ollama is installed and running, then try again."
            messages.append({"role": "assistant", "content": assistant_text})
            return assistant_text, messages

    messages.append({"role": "assistant", "content": response.message.content})
    return response.message.content, messages


def main() -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hello! I'm Finley, your First National Bank assistant. Please enter your customer ID to continue."},
    ]
    print("Finley: Hello! I'm Finley, your First National Bank assistant. Please enter your customer ID to continue.")
    print('\nType "quit" to end the chat.\n')

    # auth loop
    cust_id = ""
    while not cust_id:
        user_input = input("Enter your customer ID: ").strip()
        if user_input.lower() in ("quit", "exit", ""):
            print("Have a nice day!")
            return
        if user_input in CUSTOMERS:
            cust_id = user_input
            print("Welcome!\n")
        else:
            print("Customer not found, please try again.\n")

    # chat loop
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("quit", "exit", ""):
            print("Have a nice day!")
            break

        assistant_text, messages = respond(messages, user_input, cust_id=cust_id)
        print("Finley:", assistant_text)


if __name__ == "__main__":
    main()