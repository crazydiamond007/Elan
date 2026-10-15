from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest
from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage
from django.urls import reverse

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


class PageInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.images = []
        self.forms = []
        self.fieldsets = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "a":
            self.links.append(attributes.get("href", ""))
        if tag == "img":
            self.images.append(attributes)
        if tag == "form":
            self.forms.append(attributes)
        if tag == "fieldset":
            self.fieldsets.append(attributes)


def inspect(response):
    page = PageInspector()
    page.feed(response.content.decode())
    return page


def test_homepage_links_reach_existing_pages_and_fragments(client):
    home = client.get(reverse("core:home"))
    parsed = inspect(home)
    assert len(parsed.ids) == len(set(parsed.ids)), "Reusable components must not duplicate IDs."
    cached = {reverse("core:home"): home}
    for href in set(parsed.links):
        assert href and href != "#", "A navigation link must have a meaningful destination."
        target = urlsplit(href)
        assert not target.scheme and not target.netloc
        destination = target.path or reverse("core:home")
        if destination not in cached:
            cached[destination] = client.get(destination)
        response = cached[destination]
        assert response.status_code == 200, destination
        if target.fragment:
            assert target.fragment in inspect(response).ids, href


@pytest.mark.parametrize(
    ("route", "present", "absent"),
    [
        ("catalog:women", "The Sculpted Wool Coat", "The Everyday Tote"),
        ("catalog:men", "The Fine Wool Knit", "The Sculpted Wool Coat"),
        ("catalog:accessories", "The Everyday Tote", "The Fine Wool Knit"),
    ],
)
def test_department_previews_show_relevant_pieces(client, route, present, absent):
    response = client.get(reverse(route))
    content = response.content.decode()
    assert present in content
    assert absent not in content
    assert "Fictional products" in content
    assert "No real purchases" in content
    for form in inspect(response).forms:
        expected = "post" if form.get("action") == reverse("marketing:newsletter") else "get"
        assert form.get("method") == expected


def test_unknown_preview_department_does_not_fall_back_to_all_pieces(client):
    assert client.get("/collection-preview/unknown/").status_code == 404


def test_homepage_images_are_local_responsive_and_have_descriptions(client):
    parsed = inspect(client.get(reverse("core:home")))
    assert parsed.images
    for image in parsed.images:
        assert image["alt"] or image.get("aria-hidden") == "true"
        assert image["width"] and image["height"]
        if image["src"].startswith("/static/"):
            assert finders.find(image["src"].removeprefix("/static/"))
        else:
            assert image["src"].startswith("/media/")
            assert default_storage.exists(image["src"].removeprefix("/media/"))
        assert "srcset" in image and "sizes" in image
    heroes = [image for image in parsed.images if image.get("fetchpriority") == "high"]
    assert len(heroes) == 1
    hero = heroes[0]
    assert hero.get("loading") != "lazy"
    assert all(image["loading"] == "lazy" for image in parsed.images if image is not hero)


def test_newsletter_form_discloses_fictional_addresses_and_local_storage(client):
    response = client.get(reverse("core:home"))
    parsed = inspect(response)
    forms = [form for form in parsed.forms if form.get("action") == reverse("marketing:newsletter")]
    assert len(forms) == 1
    assert forms[0]["method"] == "post"
    assert b"fictional address" in response.content
    assert b"Stored locally; no email is sent" in response.content
    assert b"csrfmiddlewaretoken" in response.content


def test_preview_is_read_only_and_keeps_demo_noindex_policy(client):
    response = client.post(reverse("core:collection_preview"))
    assert response.status_code == 405
    assert "noindex" in response["X-Robots-Tag"]


def test_old_preview_links_redirect_to_database_catalog(client):
    for old, new in [
        ("/collection-preview/", "/shop/"),
        ("/collection-preview/women/", "/shop/women/"),
        ("/collection-preview/men/", "/shop/men/"),
        ("/collection-preview/accessories/", "/shop/accessories/"),
    ]:
        response = client.get(old)
        assert response.status_code == 301
        assert response.url == new
