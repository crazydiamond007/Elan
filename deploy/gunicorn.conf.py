"""Bounded defaults for this Django WSGI monolith; override bind/workers explicitly."""

import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
if not 1 <= workers <= 8:
    raise ValueError("WEB_CONCURRENCY must be between 1 and 8.")
worker_class = "sync"
timeout = 30
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
control_socket_disable = True
# Do not log query strings, request bodies, credentials or cookie values.
access_log_format = "%(m)s %(U)s %(s)s %(L)s"
# Gunicorn must not silently trust forwarding headers from arbitrary peers.
forwarded_allow_ips = os.environ.get("GUNICORN_FORWARDED_ALLOW_IPS", "")
if "*" in forwarded_allow_ips:
    raise ValueError("Use explicit trusted proxy IPs in GUNICORN_FORWARDED_ALLOW_IPS.")
