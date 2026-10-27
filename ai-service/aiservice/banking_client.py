"""HTTP client for the banking microservice (standard library only).

The banking API is protected by HTTP Basic auth (Spring Security, local demo
user — see the banking service README section "Demo auth"). Credentials
come from the BANKING_AUTH_USER / BANKING_AUTH_PASS environment variables
and are only sent when both are set; with no credentials configured, no
Authorization header is sent (this keeps local tests against an open stub
server working unchanged).
"""

import base64
import json
import os
import urllib.error
import urllib.request


class BankingClient:
    """Calls the Spring Boot banking REST APIs over HTTP."""

    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = (base_url or os.environ.get(
            "BANKING_BASE_URL", "http://localhost:8080")).rstrip("/")
        self.username = username if username is not None else os.environ.get(
            "BANKING_AUTH_USER")
        self.password = password if password is not None else os.environ.get(
            "BANKING_AUTH_PASS")

    def _headers(self):
        if self.username and self.password:
            token = base64.b64encode(
                f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {token}"}
        return {}

    def _get(self, path):
        req = urllib.request.Request(self.base_url + path, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            raise BankingError(f"Banking service returned HTTP {e.code}: {body}")
        except Exception as e:
            raise BankingError(f"Could not reach banking service: {e}")

    def get_account(self, account_id):
        return self._get(f"/api/accounts/{account_id}")

    def get_balance(self, account_id):
        account = self.get_account(account_id)
        return account["balance"]

    def list_transactions(self, account_id):
        return self._get(f"/api/accounts/{account_id}/transactions")


class BankingError(Exception):
    pass
