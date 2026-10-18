from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from apps.core.views import review_media

admin.site.site_header = "MAISON ÉLAN administration"
admin.site.site_title = "MAISON ÉLAN"
admin.site.index_title = "Site administration"

urlpatterns = [
    path("", include("apps.catalog.urls")),
    path("", include("apps.cart.urls")),
    path("", include("apps.checkout.urls")),
    path("", include("apps.marketing.urls")),
    path("", include("apps.core.urls")),
]

if not getattr(settings, "LAN_PREVIEW", False):
    urlpatterns.insert(0, path("admin/", admin.site.urls))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "LOCAL_REVIEW", False):
    urlpatterns += [re_path(r"^media/products/(?P<path>[0-9]+/[a-f0-9]{32}\.webp)$", review_media)]

handler400 = "apps.core.views.bad_request"
handler403 = "apps.core.views.permission_denied"
handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"
