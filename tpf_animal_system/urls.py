"""
URL configuration for tpf_animal_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
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
    path('accounts/', include('accounts.urls')),
    path('core', include('core.urls')),
    path('dashboard/', dashboard_redirect, name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'horse', 'core', 'static'))
