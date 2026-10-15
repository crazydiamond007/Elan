import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from apps.core.proxy import TrustedClientAddressMiddleware


@pytest.mark.parametrize(
    ("networks", "peer", "header", "expected"),
    [
        ([], "192.0.2.1", "203.0.113.1", "192.0.2.1"),
        (["127.0.0.1/32"], "192.0.2.1", "203.0.113.1", "192.0.2.1"),
        (["127.0.0.1/32"], "127.0.0.1", "203.0.113.1", "203.0.113.1"),
        (["127.0.0.1/32"], "127.0.0.1", "203.0.113.1, 192.0.2.2", "127.0.0.1"),
        (["::1/128"], "::1", "2001:db8::1", "2001:db8::1"),
        ([], "bad", "203.0.113.1", "unknown"),
    ],
)
def test_only_listed_socket_peers_can_supply_a_single_client_address(
    settings, networks, peer, header, expected
):
    settings.TRUSTED_PROXY_NETWORKS = networks
    request = RequestFactory().get("/", REMOTE_ADDR=peer, HTTP_X_REAL_IP=header)
    TrustedClientAddressMiddleware(lambda request: HttpResponse())(request)
    assert request.client_ip == expected
