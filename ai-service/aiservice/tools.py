"""Tool registry: the agent's only way to read live banking data.

The agent NEVER guesses a balance or transaction list. When a question needs
live data, it calls one of these tools, which hit the banking service's REST
APIs. Tool results are quoted back to the user as facts from the service.
"""

import re

from .banking_client import BankingClient, BankingError

UUID_LIKE = re.compile(r"[0-9a-fA-F-]{8,}")


class Tool:
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func

    def call(self, **kwargs):
        return self.func(**kwargs)


def build_tools(banking_client=None):
    """Return the tool registry backed by the given (or default) client."""
    client = banking_client or BankingClient()

    def get_balance(account_id):
        try:
            balance = client.get_balance(account_id)
            return {"balance": balance, "account_id": account_id}
        except BankingError as e:
            return {"error": str(e)}

    def list_transactions(account_id, limit=5):
        try:
            txs = client.list_transactions(account_id)
            return {"transactions": txs[-limit:], "account_id": account_id}
        except BankingError as e:
            return {"error": str(e)}

    return {
        "get_balance": Tool(
            "get_balance",
            "Get the current balance of an account. Needs account_id.",
            get_balance),
        "list_transactions": Tool(
            "list_transactions",
            "List recent transactions of an account. Needs account_id.",
            list_transactions),
    }


def extract_account_id(question, fallback=None):
    """Pull an account id out of the question text, if one is present."""
    match = UUID_LIKE.search(question or "")
    if match:
        return match.group(0)
    return fallback
