"""Unit tests for NotificationDispatcher."""

from core.notifier import NotificationDispatcher


def test_notifier_no_token():
    notifier = NotificationDispatcher(token="")
    assert notifier.post_github_digest({}, "https://github.com/Raj123-0/test", 5) is False


def test_notifier_no_discord_webhook():
    notifier = NotificationDispatcher(token="")
    assert notifier.send_discord_notification({}, "https://github.com/Raj123-0/test", 5) is False
