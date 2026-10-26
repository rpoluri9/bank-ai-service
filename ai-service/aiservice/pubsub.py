"""Event publishing: local by default, Google Cloud Pub/Sub when configured.

Mirrors the banking service's publisher interface. The local publisher keeps
events in memory and logs them, so the whole platform runs offline. The REST
publisher calls the Pub/Sub REST API and is only used when PUBSUB_ENABLED=1
plus PUBSUB_PROJECT_ID, PUBSUB_TOPIC, and PUBSUB_ACCESS_TOKEN are set.
"""

import base64
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)


class LocalEventPublisher:
    """Default publisher: in-memory + logged. No cloud setup needed."""

    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)
        log.info("EVENT (local publisher): %s", json.dumps(event))


class PubSubRestPublisher:
    """Publishes to a real Pub/Sub topic via the REST API (needs credentials)."""

    def __init__(self, project_id, topic, access_token):
        self.project_id = project_id
        self.topic = topic
        self.access_token = access_token

    def publish(self, event):
        data = base64.b64encode(json.dumps(event).encode("utf-8")).decode("ascii")
        body = json.dumps({"messages": [{"data": data}]}).encode("utf-8")
        url = (f"https://pubsub.googleapis.com/v1/projects/{self.project_id}"
               f"/topics/{self.topic}:publish")
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Authorization": f"Bearer {self.access_token}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if not (200 <= resp.status < 300):
                raise RuntimeError(f"Pub/Sub publish failed: HTTP {resp.status}")


def build_publisher():
    """Local publisher unless Pub/Sub is explicitly configured."""
    if os.environ.get("PUBSUB_ENABLED") == "1":
        project_id = os.environ.get("PUBSUB_PROJECT_ID", "")
        topic = os.environ.get("PUBSUB_TOPIC", "")
        token = os.environ.get("PUBSUB_ACCESS_TOKEN", "")
        if project_id and topic and token:
            return PubSubRestPublisher(project_id, topic, token)
    return LocalEventPublisher()
