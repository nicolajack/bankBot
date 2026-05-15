from ollama import chat
from ollama import ChatResponse
import json
# generate fake data on run
import generate_data

MODEL = "llama3.2"

# load data
with open('mockData/accounts.json', 'r') as f:
    ACCOUNTS = json.load(f)
with open('mockData/customers.json', 'r') as f:
    CUSTOMERS = json.load(f)
with open('mockData/transactions.json', 'r') as f:
    TXNS = json.load(f)

# tool to return the blaance for an account
def get_balance(account_id: str, cust_id: str):
    """Return the balance for an account if it belongs to the given customer."""

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

# tool to return recent txns for an account
def get_recent_transactions(account_id: str, cust_id: str, limit: int = 5):
    """Return the most recent transactions for an account if it belongs to the given customer."""

    account_id = str(account_id)
    account = ACCOUNTS.get(account_id)
    if not account:
        return {"error": f"Account '{account_id}' not found."}
    if str(account.get("custID")) != str(cust_id):
        return {"error": "Account does not belong to the current customer."}

    # in case limit is not included
    if limit is None:
        limit = 5
    else: 
        limit = int(limit)
    limit = max(1, limit)

    # match txns to account id
    matching = [txn for txn in TXNS.values() if str(txn.get("accountID")) == account_id]

    # sort by txn date
    matching.sort(key=lambda t: (t.get("transactionDate") or ""), reverse=True)
    recent = matching[:limit]

    # keep only fields we want to show
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

# define tools 
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
                    "description": "The account ID to get the balance for (this is the key in accounts.json, e.g. '17')"
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
                    "description": "Maximum number of transactions to return",
                    "default": 5
                }
            },
            "required": ["account_id"]
        }
    }
}

TOOLS = [get_balance_tool, get_recent_transactions_tool]
# define some more tools here once these work

TOOL_FUNCTIONS = {
    "get_balance": get_balance,
    "get_recent_transactions": get_recent_transactions,
}

def dispatch_tool(name, args):
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    return fn(**args)

SYSTEM_PROMPT = ('You are an AI assistant that works for "First National Bank." Your name is Finley. Your purpose is to provide personalized and secure financial assistance to users of the banking application. '
        'Scope: Access user data, including account information, transaction history, and personal preferences. Collect additional data from external sources with user consent. Answer user queries on various banking topics, such as account management, transactions, and payment schedules. Provide personalize recommendations for budgeting, savings, and investment opportunities. Assist users in resolving basic banking issues, like forgotten passwords or missing checks. Ensure all interactions are secure. Monitor system logs for suspicious activity and alert administrators accordingly. '
        'Limit and Exceptions: Do not access or provide sensitive information that could compromise user security. Refrain from making decisions or taking actions that would affect users\' financial well-being. Avoid providing explicit content. Only respond to user queries within the scope of your programming and training data, and refuse off-topic requests.'
        'Communication Protocol: Use natural language processing techniques to understand user inputs and generate human-like responses. Employ tone and language that is empathetic, concise, and easy to understand. Provide clear explanations for system limitations and exceptions when necessary. Never return raw JSON to the user.'
        'Monitoring and Updates: Regularly review and update your training data to ensure accuracy and relevance. Conduct regular self-evaluation exercises to identify areas for improvement. Collaborate with human administrators to address any concerns or discepancies in user interactions.'
        'Tool Calls: If you want to call a tool, you should have all necessary information for it from the user. If you do not, simply ask the user for any missing information.')

# intialize convo, set system prompt
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "assistant", "content": "Hello! I'm Finley, your First National Bank assistant. Please enter your customer ID to continue."},
]
print("Finley: Hello! I'm Finley, your First National Bank assistant. Please enter your customer ID to continue.")
print('\nType "quit" to end the chat.\n')

# auth loop
custId = ""
while not custId:
    userInput = input("Enter your customer ID: ")
    userInput = userInput.lower()
    if userInput.lower() in ("quit", "exit", ""):
        print("Have a nice day!")
        exit()
    # then check if userInput is in customers
    if userInput in CUSTOMERS:
        custId = userInput
        print("Welcome!\n")
    else: 
        print("Customer not found, please try again.\n")

# chat loop
while True:
    userInput = input("User: ")
    if userInput.lower() in ("quit", "exit", ""):
        print("Have a nice day!")
        break

    messages.append({"role": "user", "content": userInput})

    # IMPORTANT: Ollama expects the tool schema objects here, not the Python function map
    response: ChatResponse = chat(model=MODEL, messages=messages, tools=TOOLS)

    # check if the model wants to call a tool
    if response.message.tool_calls:
        # add the assistant's response (with tool call intent) to messages
        messages.append({
            "role": "assistant",
            "content": response.message.content,
            "tool_calls": response.message.tool_calls,
        })

        # process each tool call through dispatch
        for tool_call in response.message.tool_calls:
            name = tool_call.function.name
            args = dict(tool_call.function.arguments or {})

            # inject authenticated customer context when required (right now is always required, can change if some funcs dont need)
            args["cust_id"] = custId

            result = dispatch_tool(name, args)

            messages.append({
                "role": "tool",
                "content": json.dumps(result),
                "name": name,
            })

        # ask the model again now that tool outputs are in the messages
        response = chat(model=MODEL, messages=messages)

    messages.append({"role": "assistant", "content": response.message.content})
    print("Finley:", response.message.content)