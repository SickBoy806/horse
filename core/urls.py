from django.urls import path
from . import views

urlpatterns = [
    # Dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # Animal management
    path('animals/', views.animal_list, name='animal_list'),
    path('animals/add/', views.add_animal, name='add_animal'),
    path('animals/<int:animal_id>/', views.view_animal_detail, name='view_animal_detail'),
    
    # Task management
    path('tasks/assign/', views.assign_vet_task, name='assign_vet_task'),
    
    # Support tickets
    path('<str:branch>/tickets/', views.ticket_list, name='ticket_list'),
    path('<str:branch>/tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<str:branch>/tickets/create/', views.ticket_create, name='ticket_create'),
    
    # Messaging
    path('messages/', views.inbox, name='inbox'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    path('messages/<int:message_id>/reply/', views.reply_message, name='reply_message'),
    
    # API endpoints
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),
    path('api/messages/unread/', views.unread_message_count_api, name='unread_message_count_api'),

    # Reports
    path('reports/', views.reports_list, name='reports_list'),
    path('reports/create/', views.create_report, name='create_report'),
    path('dashboard/training/', views.training_dashboard, name='training_dashboard'),
]
