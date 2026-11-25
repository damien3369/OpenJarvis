"""`jarvis connect gmail_imap` must prompt for email + app password."""

import click
from click.testing import CliRunner

from openjarvis.cli import connect_cmd


class _FakeIMAP:
    auth_type = "oauth"  # same as the real gmail_imap connector
    received = None

    def is_connected(self):
        return False

    def auth_url(self):
        return "https://myaccount.google.com/apppasswords"

    def connect_with_credentials(self, email, password):
        _FakeIMAP.received = (email, password)


class _Registry:
    def contains(self, key):
        return key == "gmail_imap"

    def get(self, key):
        return _FakeIMAP

    def keys(self):
        return ["gmail_imap"]


def test_app_password_flow_strips_spaces_and_skips_oauth():
    @click.command()
    def cmd():
        connect_cmd._connect_source(_Registry(), "gmail_imap")

    result = CliRunner().invoke(cmd, input="moi@gmail.com\nabcd efgh ijkl mnop\n")
    assert result.exit_code == 0, result.output
    assert "No OAuth provider" not in result.output
    assert "connected successfully" in result.output
    assert _FakeIMAP.received == ("moi@gmail.com", "abcdefghijklmnop")
