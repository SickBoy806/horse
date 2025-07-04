from django.urls import path
from . import views

urlpatterns = [
    path('<str:branch>/tickets/', views.ticket_list, name='ticket_list'),
    path('<str:branch>/tickets/create/', views.ticket_create, name='ticket_create'),
    path('<str:branch>/tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<str:branch>/tickets/<int:ticket_id>/close/', views.ticket_close, name='ticket_close'),
]