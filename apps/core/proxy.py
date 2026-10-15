from ipaddress import ip_address, ip_network

from django.conf import settings


class TrustedClientAddressMiddleware:
    """Only a listed socket peer may supply a single proxy-overwritten X-Real-IP."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.networks = [ip_network(value) for value in settings.TRUSTED_PROXY_NETWORKS]

    def __call__(self, request):
        raw = request.META.get("REMOTE_ADDR", "")
        try:
            peer = ip_address(raw)
            request.client_ip = str(peer)
            if any(peer in network for network in self.networks):
                try:
                    request.client_ip = str(ip_address(request.META.get("HTTP_X_REAL_IP", "")))
                except ValueError:
                    pass
        except ValueError:
            request.client_ip = "unknown"
        return self.get_response(request)
