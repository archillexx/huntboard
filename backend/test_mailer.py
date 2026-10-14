import pytest
import resend

from mailer import EmailNotSent, send_email


def test_dev_mode_prints_instead_of_sending(monkeypatch, capsys):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)

    send_email("bob@example.com", "Your code", "123456")

    printed = capsys.readouterr().out
    assert "bob@example.com" in printed
    assert "123456" in printed


def test_production_without_a_key_refuses_to_print(monkeypatch, capsys):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(EmailNotSent):
        send_email("bob@example.com", "Your code", "123456")

    assert "123456" not in capsys.readouterr().out


def test_provider_errors_become_email_not_sent(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_fake_key_for_tests")

    # Stand-in for Resend: fail the way the real library does, without touching the network.
    def fail(params):
        raise resend.exceptions.ResendError(code=500, error_type="application_error", message="boom", suggested_action="")

    monkeypatch.setattr(resend.Emails, "send", fail)

    with pytest.raises(EmailNotSent):
        send_email("bob@example.com", "Your code", "123456")
