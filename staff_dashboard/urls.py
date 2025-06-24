from django.urls import path
from .views import staff_dashboard

urlpatterns = [
    path('<str:branch>/', staff_dashboard, name='staff_dashboard'),
]