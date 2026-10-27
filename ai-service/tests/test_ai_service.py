"""Tests for the Bank AI Platform Python AI service (stdlib unittest)."""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from aiservice.agent import BankAgent
from aiservice.banking_client import BankingClient
from aiservice.documents import DOCUMENTS
from aiservice.ingestion import build_index, chunk_text
from aiservice.providers import LocalModelProvider
from aiservice.pubsub import LocalEventPublisher
from aiservice.tools import build_tools


class StubBankingHandler(BaseHTTPRequestHandler):
    """Tiny fake of the Spring Boot banking API for tool tests."""

    def do_GET(self):
        if self.path == "/api/accounts/acc-1":
            body = {"id": "acc-1", "ownerName": "Ramesh",
                    "accountType": "SAVINGS", "balance": 1250.5}
        elif self.path == "/api/accounts/acc-1/transactions":
            body = [
                {"id": "t1", "type": "DEPOSIT", "amount": 500,
                 "balanceAfter": 1250.5},
                {"id": "t2", "type": "WITHDRAWAL", "amount": 100,
                 "balanceAfter": 750.5},
            ]
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"message":"Account not found"}')
            return
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class IngestionTests(unittest.TestCase):
    def test_chunking_splits_long_documents(self):
        long_text = " ".join(f"Sentence number {i} about fees." for i in range(200))
        chunks = chunk_text(long_text, max_chars=800)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 800)

    def test_index_contains_all_seed_documents(self):
        index = build_index(DOCUMENTS)
        doc_ids = {c["doc_id"] for c in index.chunks}
        self.assertEqual(doc_ids, {d["id"] for d in DOCUMENTS})


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.index = build_index(DOCUMENTS)

    def test_fee_question_finds_fee_schedule(self):
        results = self.index.search("What is the overdraft fee?", top_k=3)
        self.assertTrue(results)
        self.assertEqual(results[0]["doc_id"], "fee-schedule")

    def test_interest_question_finds_account_policies(self):
        results = self.index.search("What interest rate do savings accounts earn?", top_k=3)
        self.assertTrue(results)
        self.assertEqual(results[0]["doc_id"], "account-policies")

    def test_unrelated_question_finds_nothing_relevant(self):
        results = self.index.search("How do I bake a chocolate cake?", top_k=3)
        self.assertEqual(results, [])


class AgentDocTests(unittest.TestCase):
    def setUp(self):
        self.agent = BankAgent(provider=LocalModelProvider())

    def test_doc_question_answered_from_documents(self):
        result = self.agent.ask("What is the overdraft fee?")
        self.assertIn("overdraft", result["answer"].lower())
        self.assertTrue(result["sources"])
        self.assertEqual(result["provider"], "local")

    def test_unanswerable_question_is_honest(self):
        result = self.agent.ask("How do I bake a chocolate cake?")
        self.assertIn("couldn't find", result["answer"])
        self.assertEqual(result["sources"], [])

    def test_balance_question_without_account_id_explains_itself(self):
        result = self.agent.ask("What is my balance?")
        self.assertIn("account id", result["answer"].lower())
        self.assertIn("get_balance", result["tools_used"])


class AgentToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), StubBankingHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _agent(self):
        client = BankingClient(base_url=f"http://127.0.0.1:{self.port}")
        return BankAgent(tools=build_tools(client), provider=LocalModelProvider())

    def test_balance_tool_returns_live_balance(self):
        result = self._agent().ask("What is my balance?", account_id="acc-1")
        self.assertIn("1250.5", result["answer"])
        self.assertIn("get_balance", result["tools_used"])

    def test_transaction_tool_returns_live_history(self):
        result = self._agent().ask("Show my recent transactions", account_id="acc-1")
        self.assertIn("DEPOSIT", result["answer"])
        self.assertIn("WITHDRAWAL", result["answer"])
        self.assertIn("list_transactions", result["tools_used"])

    def test_tool_error_is_reported_not_guessed(self):
        result = self._agent().ask("What is my balance?", account_id="missing")
        self.assertIn("could not be reached", result["answer"].lower()
                      .replace("banking service", "banking service"))
        self.assertIn("get_balance", result["tools_used"])


class PublisherTests(unittest.TestCase):
    def test_local_publisher_records_events(self):
        publisher = LocalEventPublisher()
        agent = BankAgent(provider=LocalModelProvider(), publisher=publisher)
        agent.ask("What is the overdraft fee?")
        self.assertEqual(len(publisher.events), 1)
        self.assertEqual(publisher.events[0]["type"], "question_answered")


class AuthHeaderTests(unittest.TestCase):
    """BankingClient sends Basic auth only when credentials are configured."""

    @classmethod
    def setUpClass(cls):
        class CapturingHandler(StubBankingHandler):
            seen = {}

            def do_GET(self):
                CapturingHandler.seen.clear()
                CapturingHandler.seen.update(self.headers)
                super().do_GET()

        cls.handler = CapturingHandler
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), CapturingHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_no_credentials_means_no_auth_header(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("BANKING_AUTH_USER", "BANKING_AUTH_PASS")}
        with mock.patch.dict(os.environ, env, clear=True):
            BankingClient(base_url=f"http://127.0.0.1:{self.port}").get_balance("acc-1")
        self.assertNotIn("Authorization", self.handler.seen)

    def test_configured_credentials_send_basic_auth(self):
        import base64
        with mock.patch.dict(os.environ, {"BANKING_AUTH_USER": "demo",
                                          "BANKING_AUTH_PASS": "demo123"}):
            BankingClient(base_url=f"http://127.0.0.1:{self.port}").get_balance("acc-1")
        expected = "Basic " + base64.b64encode(b"demo:demo123").decode("ascii")
        self.assertEqual(expected, self.handler.seen.get("Authorization"))


if __name__ == "__main__":
    unittest.main()
