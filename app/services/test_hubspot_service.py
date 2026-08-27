"""Unit tests for HubSpot credential parsing (refresh owned by Integrations inject)."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from app.services.hubspot_service import HubSpotError, HubSpotService


class HubSpotServiceTests(unittest.TestCase):
    def test_accepts_token_or_access_token(self):
        self.assertEqual(
            HubSpotService(credentials_json=json.dumps({"token": "abc"}))._token, "abc"
        )
        self.assertEqual(
            HubSpotService(credentials_json=json.dumps({"access_token": "xyz"}))._token, "xyz"
        )

    def test_missing_credentials(self):
        with self.assertRaises(HubSpotError) as ctx:
            HubSpotService()
        self.assertEqual(ctx.exception.error_code, "CREDENTIALS_REQUIRED")

    def test_401_is_auth_error_without_local_refresh(self):
        resp = MagicMock()
        resp.status_code = 401
        resp.text = "expired"
        with patch("app.services.hubspot_service.requests.request", return_value=resp) as req:
            svc = HubSpotService(credentials_json=json.dumps({"token": "stale"}))
            with self.assertRaises(HubSpotError) as ctx:
                svc.search("contacts", "q", 5)
        self.assertEqual(ctx.exception.error_code, "AUTH_ERROR")
        self.assertEqual(req.call_count, 1)


if __name__ == "__main__":
    unittest.main()
