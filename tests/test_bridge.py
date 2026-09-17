"""Unit tests for EcosystemBridge."""

from core.bridge import EcosystemBridge


def test_bridge_no_token():
    bridge = EcosystemBridge(token="")
    assert bridge.register_new_repo("test-repo", "computational_math") is False


def test_bridge_headers():
    bridge = EcosystemBridge(token="my-token")
    headers = bridge.headers
    assert "Bearer my-token" in headers["Authorization"]
