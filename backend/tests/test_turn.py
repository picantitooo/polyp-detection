import asyncio
import base64
import hashlib
import hmac
import unittest
from unittest.mock import patch

from fastapi import FastAPI

from app import config
from app.turn import generate_turn_credentials
from app.webrtc import peer_configuration, router


async def request_ice():
    # Exercise the actual ASGI route without requiring httpx or loading ONNX.
    app = FastAPI()
    app.include_router(router)
    messages = []
    scope = {"type": "http", "method": "GET", "path": "/webrtc/ice-servers",
             "query_string": b"", "headers": [], "scheme": "http",
             "server": ("test", 80), "client": ("test", 123), "http_version": "1.1"}
    async def receive():
        return {"type": "http.request", "body": b""}
    async def send(message):
        messages.append(message)
    await app(scope, receive, send)
    import json
    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start, json.loads(body)


class TurnTests(unittest.TestCase):
    def test_deterministic_hmac(self):
        result = generate_turn_credentials("test-secret", 3600, now=1700000000, identifier="abc")
        self.assertEqual(result["username"], "1700003600:abc")
        # Fixed vector, calculated independently with OpenSSL.
        self.assertEqual(result["credential"], "K8mZJIqxVx2ZuqBUCr6YGvy+qsk=")

    def test_expiry_and_random_identity(self):
        with patch("app.turn.time.time", return_value=1700000000.9):
            first = generate_turn_credentials("test", 60)
            second = generate_turn_credentials("test", 60)
        self.assertRegex(first["username"], r"^1700000060:[0-9a-f]{32}$")
        self.assertNotEqual(first["username"], second["username"])
        with self.assertRaises(ValueError):
            generate_turn_credentials("test", 0)

    def test_endpoint_without_turn(self):
        for url, secret in [("", ""), ("turn:example.test:3478", ""), ("", "test")]:
            with self.subTest(url=url, secret=secret), patch.object(config, "TURN_URL", url), patch.object(config, "TURN_SHARED_SECRET", secret):
                start, body = asyncio.run(request_ice())
                self.assertEqual(start["status"], 200)
                self.assertEqual(body, {"iceServers": []})
                self.assertEqual(peer_configuration().iceServers, [])

    def test_endpoint_and_backend_have_independent_credentials(self):
        with patch.object(config, "TURN_URL", "turn:example.test:3478?transport=udp"), patch.object(config, "TURN_SHARED_SECRET", "test-secret"), patch.object(config, "TURN_CREDENTIAL_TTL_SECONDS", 60), patch("app.turn.time.time", return_value=1700000000):
            start, body = asyncio.run(request_ice())
            server = body["iceServers"][0]
            self.assertEqual(start["status"], 200)
            self.assertIn((b"cache-control", b"no-store"), start["headers"])
            self.assertEqual(server["urls"], config.TURN_URL)
            self.assertTrue(server["username"].startswith("1700000060:"))
            self.assertEqual(server["credential"], base64.b64encode(hmac.new(b"test-secret", server["username"].encode(), hashlib.sha1).digest()).decode())
            backend_server = peer_configuration().iceServers[0]
            self.assertEqual(backend_server.urls, server["urls"])
            self.assertNotEqual(backend_server.username, server["username"])
            self.assertNotIn("test-secret", str(body))


if __name__ == "__main__":
    unittest.main()
