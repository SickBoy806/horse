from django.urls import path
from . import views, deployment_views, team_views, health_views, horse_views, stock_views

urlpatterns = [
    # Dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # Animal management
    path('animals/', views.animal_list, name='animal_list'),
    path('animals/add/', views.add_animal, name='add_animal'),
    path('animals/<int:animal_id>/', views.view_animal_detail, name='view_animal_detail'),
    path('animals/<int:animal_id>/edit/', views.edit_animal, name='edit_animal'),

    # Stores
    path('stock/', stock_views.stock_list, name='stock_list'),
    path('stock/new/', stock_views.stock_item_edit, name='stock_item_create'),
    path('stock/<int:item_id>/', stock_views.stock_detail, name='stock_detail'),
    path('stock/<int:item_id>/edit/', stock_views.stock_item_edit, name='stock_item_edit'),

    # Horse care: farrier, tack, stables & kennels
    path('horse-care/', horse_views.horse_care_overview, name='horse_care'),
    path('horse-care/farrier/', horse_views.farrier_log, name='farrier_log'),
    path('horse-care/tack/', horse_views.tack_list, name='tack_list'),
    path('horse-care/tack/new/', horse_views.tack_edit, name='tack_create'),
    path('horse-care/tack/<int:item_id>/edit/', horse_views.tack_edit, name='tack_edit'),
    path('horse-care/tack/<int:item_id>/inspect/', horse_views.tack_inspect, name='tack_inspect'),
    path('horse-care/stables/', horse_views.stables_board, name='stables_board'),
    path('horse-care/stables/move/', horse_views.housing_move, name='housing_move'),
    path('horse-care/stables/units/new/', horse_views.housing_unit_save, name='housing_unit_create'),
    path('horse-care/stables/units/<int:unit_id>/', horse_views.housing_unit_save, name='housing_unit_update'),
    path('horse-care/stables/stays/<int:assignment_id>/end/', horse_views.housing_vacate, name='housing_vacate'),

    # Preventive care schedule
    path('health/', health_views.health_schedule, name='health_schedule'),

    # Handler teams & certifications
    path('teams/', team_views.teams_roster, name='teams_roster'),
    path('animals/<int:animal_id>/handlers/assign/', team_views.assign_handler, name='assign_handler'),
    path('handlers/<int:assignment_id>/end/', team_views.end_assignment, name='end_assignment'),
    path('animals/<int:animal_id>/certifications/add/', team_views.add_certification, name='add_certification'),
    path('certifications/<int:cert_id>/delete/', team_views.delete_certification, name='delete_certification'),

    # Deployments
    path('deployments/', deployment_views.deployment_list, name='deployment_list'),
    path('deployments/new/', deployment_views.deployment_form, name='deployment_create'),
    path('deployments/<int:deployment_id>/', deployment_views.deployment_detail, name='deployment_detail'),
    path('deployments/<int:deployment_id>/edit/', deployment_views.deployment_form, name='deployment_edit'),
    path('animals/<int:animal_id>/status/', views.animal_set_status, name='animal_set_status'),

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

    # Training
    path('dashboard/training/', views.training_dashboard, name='training_dashboard'),
    path('dashboard/training/sessions/', views.training_sessions, name='training_sessions'),
    path('dashboard/training/progression/', views.training_progression, name='training_progression'),
]