"""Model providers: Google ADK-style agent orchestration with a Vertex AI
provider interface, plus a local fallback that always works.

How provider selection works (honest version):
- If VERTEX_PROJECT_ID, VERTEX_LOCATION, VERTEX_MODEL, and
  VERTEX_ACCESS_TOKEN are all set, the agent uses VertexAiProvider, which
  calls the Vertex AI REST API (generateContent) with the agent's instructions
  and the retrieved context.
- Otherwise the agent uses LocalModelProvider, which composes the answer from
  the retrieved document chunks and tool results with plain templates. No
  model download, no API key, no network needed.

The agent loop itself (instructions -> tool planning -> tool calls -> final
answer) is identical either way; only the final text-composition step swaps.
"""

import json
import os
import urllib.request


class LocalModelProvider:
    """Template-based answer composer. Runs fully offline."""

    name = "local"

    def compose(self, question, tool_results, doc_chunks):
        parts = []
        for tool_name, result in tool_results:
            if "error" in result:
                parts.append(
                    f"I tried to look that up with the {tool_name} tool, but "
                    f"the banking service could not be reached: {result['error']}")
            elif tool_name == "get_balance":
                parts.append(
                    f"Your current balance is {result['balance']} "
                    f"(account {result['account_id']}).")
            elif tool_name == "list_transactions":
                txs = result["transactions"]
                if not txs:
                    parts.append("No transactions found for that account yet.")
                else:
                    lines = [
                        f"- {t['type']} of {t['amount']} "
                        f"(balance after: {t['balanceAfter']})"
                        for t in txs
                    ]
                    parts.append("Your recent transactions:\n" + "\n".join(lines))
        for chunk in doc_chunks:
            parts.append(
                f"From the bank's {chunk['title']}: {chunk['text']}")
        if not parts:
            return None
        return "\n\n".join(parts)


class VertexAiProvider:
    """Calls Vertex AI's generateContent REST API.

    Requires real GCP credentials (project id, location, model, and an OAuth
    access token). This provider is never used unless all four values are
    configured; see build_provider().
    """

    name = "vertex-ai"

    def __init__(self, project_id, location, model, access_token):
        self.project_id = project_id
        self.location = location
        self.model = model
        self.access_token = access_token

    def compose(self, question, tool_results, doc_chunks):
        context = []
        for tool_name, result in tool_results:
            context.append(f"Tool {tool_name} returned: {json.dumps(result)}")
        for chunk in doc_chunks:
            context.append(
                f"Document {chunk['title']}: {chunk['text']}")
        prompt = (
            "You are a helpful bank assistant. Answer the question using only "
            "the context below. If the context does not contain the answer, "
            "say so honestly.\n\n"
            + "\n".join(context)
            + f"\n\nQuestion: {question}"
        )
        url = (f"https://{self.location}-aiplatform.googleapis.com/v1/"
               f"projects/{self.project_id}/locations/{self.location}/"
               f"publishers/google/models/{self.model}:generateContent")
        body = json.dumps({
            "contents": [{"role": "user",
                          "parts": [{"text": prompt}]}]
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Authorization": f"Bearer {self.access_token}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        try:
            return payload["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return None


def build_provider():
    """Vertex AI when fully configured, otherwise the local provider."""
    project_id = os.environ.get("VERTEX_PROJECT_ID", "")
    location = os.environ.get("VERTEX_LOCATION", "us-central1")
    model = os.environ.get("VERTEX_MODEL", "gemini-1.5-flash")
    token = os.environ.get("VERTEX_ACCESS_TOKEN", "")
    if project_id and token:
        return VertexAiProvider(project_id, location, model, token)
    return LocalModelProvider()
