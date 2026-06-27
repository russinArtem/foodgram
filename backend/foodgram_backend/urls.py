from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('recipes.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        path(
            'redoc/',
            TemplateView.as_view(
                template_name='redoc.html',
                extra_context={'schema_url': '/redoc/openapi-schema.yml'}
            ),
            name='redoc'
        ),
        path(
            'redoc/openapi-schema.yml',
            serve,
            {
                'document_root': settings.BASE_DIR / 'docs',
                'path': 'openapi-schema.yml'
            },
            name='openapi-schema'
        ),
    ]
