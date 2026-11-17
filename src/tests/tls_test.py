import ssl
from unittest.mock import patch

import pytest

from smart_home_automation.common.tls import create_client_context
from smart_home_automation.control_panel import _parse_arguments as parse_panel_arguments
from smart_home_automation.server import _parse_arguments as parse_server_arguments
from smart_home_automation.server.server import Server


def test_client_context_uses_configured_ca_file():
    expected_context = object()

    with patch("ssl.create_default_context", return_value=expected_context) as create_context:
        context = create_client_context("ca.crt")

    assert context is expected_context
    create_context.assert_called_once_with(cafile="ca.crt")


def test_server_requires_certificate_and_key_together():
    with pytest.raises(ValueError, match="provided together"):
        Server(cert_file="server.crt")


def test_server_tls_arguments_are_parsed():
    arguments = parse_server_arguments(["--cert-file", "server.crt", "--key-file", "server.key"])

    assert arguments.cert_file == "server.crt"
    assert arguments.key_file == "server.key"


def test_server_rejects_partial_tls_arguments():
    with pytest.raises(SystemExit):
        parse_server_arguments(["--cert-file", "server.crt"])


def test_control_panel_ca_file_argument_is_parsed():
    arguments = parse_panel_arguments(["--ca-file", "ca.crt"])

    assert arguments.ca_file == "ca.crt"


def test_client_context_is_configured_for_server_verification():
    context = ssl.create_default_context()

    assert context.verify_mode is ssl.CERT_REQUIRED
    assert context.check_hostname is True
