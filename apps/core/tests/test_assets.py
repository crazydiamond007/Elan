import os

from django.test import override_settings

from apps.core.templatetags.metadata import stylesheet_url


def test_development_stylesheet_url_changes_after_a_rebuild(settings, tmp_path):
    settings.DEBUG = True
    settings.STATICFILES_DIRS = [tmp_path]
    stylesheet = tmp_path / "search.css"
    stylesheet.write_text("dialog { height: auto; }")
    first = stylesheet_url("search.css")
    assert first.startswith("/static/search.css?v=")
    assert stylesheet_url("search.css") == first
    timestamp = stylesheet.stat().st_mtime_ns
    os.utime(stylesheet, ns=(timestamp, timestamp + 1_000_000_000))
    assert stylesheet_url("search.css") != first


@override_settings(DEBUG=False)
def test_non_debug_stylesheet_url_uses_configured_static_storage():
    assert stylesheet_url("css/app.css") == "/static/css/app.css"
