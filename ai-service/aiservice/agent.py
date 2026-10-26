"""Google ADK-style agent loop.

The agent follows fixed instructions, plans which tools a question needs,
calls those tools (never guessing live data), retrieves document context for
everything else, and composes a final answer through the configured model
provider. A question can trigger both a tool call and a document lookup in
the same turn (multi-step), e.g. 'what is my balance and what is the savings
interest rate?'
"""

import re

from .documents import DOCUMENTS
from .ingestion import build_index
from .providers import build_provider
from .tools import build_tools, extract_account_id

AGENT_INSTRUCTIONS = (
    "You are a helpful bank assistant. Use tools for live banking data "
    "(balances, transactions) and bank documents for policies, fees, and FAQs. "
    "Never invent a balance, a transaction, or a policy. If neither tools nor "
    "documents contain the answer, say so honestly."
)

BALANCE_WORDS = {"balance", "how much", "money", "funds"}
TRANSACTION_WORDS = {"transaction", "transactions", "history", "statement",
                     "activity", "recent"}


class BankAgent:
    """The agent: instructions + tool registry + retrieval + provider."""

    def __init__(self, tools=None, provider=None, index=None, publisher=None):
        self.tools = tools or build_tools()
        self.provider = provider or build_provider()
        self.index = index or build_index(DOCUMENTS)
        self.publisher = publisher

    def _plan_tools(self, question):
        """Decide which tools the question needs, from its wording."""
        lowered = question.lower()
        wants = []
        if any(word in lowered for word in BALANCE_WORDS):
            wants.append("get_balance")
        if any(word in lowered for word in TRANSACTION_WORDS):
            wants.append("list_transactions")
        return wants

    def ask(self, question, account_id=None):
        """Run one agent turn. Returns a dict with answer + evidence."""
        account_id = extract_account_id(question, account_id)
        tool_results = []
        tools_used = []
        for tool_name in self._plan_tools(question):
            if account_id is None:
                tool_results.append((tool_name, {
                    "error": "No account id was provided, so I cannot look "
                             "this up. Pass account_id with your question."}))
                tools_used.append(tool_name)
                continue
            tool = self.tools[tool_name]
            result = tool.call(account_id=account_id)
            tool_results.append((tool_name, result))
            tools_used.append(tool_name)

        doc_chunks = self.index.search(question, top_k=3)
        # Only cite documents when they are actually relevant. A weak match
        # (tiny cosine score) is treated as no match, not as an answer.
        doc_chunks = [c for c in doc_chunks if c["score"] >= 0.05]

        answer = self.provider.compose(question, tool_results, doc_chunks)
        if answer is None:
            answer = ("I couldn't find a confident answer in the bank's "
                      "documents, and no live banking data applies to this "
                      "question. Please rephrase it, or ask about a fee, a "
                      "policy, your balance, or your recent transactions.")

        sources = [{"title": c["title"], "doc_id": c["doc_id"],
                    "score": c["score"]} for c in doc_chunks]
        result = {
            "answer": answer,
            "sources": sources,
            "tools_used": tools_used,
            "provider": self.provider.name,
        }
        if self.publisher is not None:
            try:
                self.publisher.publish({
                    "type": "question_answered",
                    "question": question,
                    "tools_used": tools_used,
                    "provider": self.provider.name,
                })
            except Exception:
                pass  # Event publishing must never break an answer.
        return result
