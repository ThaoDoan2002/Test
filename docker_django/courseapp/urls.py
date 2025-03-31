from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.i18n import i18n_patterns, set_language
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from courses.admin import admin_site

schema_view = get_schema_view(
    openapi.Info(
        title="EnglishCourse API",
        default_version='v1',
        description="APIs for CourseApp",
        contact=openapi.Contact(email="2151013090thao@ou.edu.vn"),
        license=openapi.License(name="Đoàn Thị Thảo@2024"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Các URL không cần đa ngôn ngữ
urlpatterns = [
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('', include('courses.urls')),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('set_language/', set_language, name='set_language'),  # Thêm đường dẫn multiple language
] + debug_toolbar_urls()

# Các URL hỗ trợ đa ngôn ngữ
urlpatterns += i18n_patterns(
    path('admin/', admin_site.urls),
)

# Thêm static URLs nếu đang ở chế độ DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
