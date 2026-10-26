"""HTTP client for the banking microservice (standard library only)."""

import json
import os
import urllib.error
import urllib.request


class BankingClient:
    """Calls the Spring Boot banking REST APIs over HTTP."""

    def __init__(self, base_url=None):
        self.base_url = (base_url or os.environ.get(
            "BANKING_BASE_URL", "http://localhost:8080")).rstrip("/")

    def _get(self, path):
        try:
            with urllib.request.urlopen(self.base_url + path, timeout=5) as resp:
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
