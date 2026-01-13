from django.contrib import admin
from django.urls import path, include
from users import views as user_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home, name='home'),

    # Include apps
    path('users/', include('users.urls')),
    path('mechanics/', include('mechanics.urls')),
    path('services/', include('services.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
