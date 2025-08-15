"""
URL configuration for tpf_animal_system project.
"""

from django.contrib import admin
from django.urls import path, include
from accounts.views import user_login, user_logout
from django.conf import settings
from django.conf.urls.static import static
from core.views import dashboard_redirect
import os

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login & Logout
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # Dashboards
    path('dashboard/', include('superadmin_dashboard.urls')),
    path('dashboard/admin/', include('admin_dashboard.urls')),
    path('dashboard/vet/', include('veterinarian_dashboard.urls')),
    path('dashboard/staff/', include('staff_dashboard.urls')),
    path('dashboard/user/', include('user_dashboard.urls')),

    # Accounts & core
    path('accounts/', include('accounts.urls')),
    path('core/', include('core.urls')),

    # Default dashboard redirect
    path('dashboard/', dashboard_redirect, name='dashboard'),
]

if settings.DEBUG:
    # Serve static files (CSS, JS, etc.)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'horse', 'core', 'static'))

    # Serve uploaded media files (photos, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
