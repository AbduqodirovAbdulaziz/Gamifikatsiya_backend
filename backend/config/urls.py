from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.classroom.urls")),
    path("api/v1/", include("apps.courses.urls")),
    path("api/v1/", include("apps.quizzes.urls")),
    path("api/v1/", include("apps.gamification.urls")),
    path("api/v1/", include("apps.competition.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/auth/", include("apps.users.auth_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

admin.site.site_header = "EduGame Boshqaruv"
admin.site.site_title = "EduGame Admin"
admin.site.index_title = "Bosh sahifa"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
