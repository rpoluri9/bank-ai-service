"""HTTP API for the AI service (standard library only).

Endpoints:
  GET  /api/health      -> {"status": "ok", "provider": "local"|"vertex-ai"}
  POST /api/ask         -> {"question": str, "account_id": str?}
                           returns {"answer", "sources", "tools_used", "provider"}
  GET  /api/documents   -> list of seeded bank document titles

Run:  python -m aiservice.server   (from the ai-service directory)
Port: 8081 by default (AI_SERVICE_PORT env var overrides).
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .agent import BankAgent
from .documents import DOCUMENTS
from .pubsub import build_publisher

logging.basicConfig(level=logging.INFO)

AGENT = BankAgent(publisher=build_publisher())


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        # CORS for the React app in the browser (demo-only: this service has
        # no auth of its own; the banking API it calls is auth-protected).
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._send_json(200, {"status": "ok", "provider": AGENT.provider.name})
        elif self.path == "/api/documents":
            self._send_json(200, [{"id": d["id"], "title": d["title"]} for d in DOCUMENTS])
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/ask":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "request body must be valid JSON"})
            return
        question = payload.get("question", "")
        if not question or not question.strip():
            self._send_json(400, {"error": "question must not be blank"})
            return
        result = AGENT.ask(question, account_id=payload.get("account_id"))
        self._send_json(200, result)

    def log_message(self, *args):
        logging.info("%s", args[0] % args[1:] if len(args) > 1 else args[0])


def main():
    port = int(os.environ.get("AI_SERVICE_PORT", "8081"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    logging.info("AI service listening on port %d (provider: %s)",
                 port, AGENT.provider.name)
    server.serve_forever()


if __name__ == "__main__":
    main()
