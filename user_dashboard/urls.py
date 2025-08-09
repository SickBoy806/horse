from django.urls import path
from .views import (
    user_dashboard,
    user_tasks,
    animal_logs,
    report_activity,
    user_messages,
    update_task_status,
    notifications_view,
    api_unread_notifications_count,
    assigned_animals,
    report_emergency,
    equipment_log_view,
    support_request_view,
)

urlpatterns = [
    path('<str:branch>/', user_dashboard, name='user_dashboard'),
    path('<str:branch>/tasks/', user_tasks, name='user_tasks'),
    path('<str:branch>/animal-logs/', animal_logs, name='animal_logs'),
    path('<str:branch>/report-activity/', report_activity, name='report_activity'),
    path('<str:branch>/messages/', user_messages, name='user_messages'),
    path('<str:branch>/tasks/update/<int:task_id>/', update_task_status, name='update_user_task'),
    path('<str:branch>/notifications/', notifications_view, name='notifications_view'),
    path('<str:branch>/api/unread-notifications-count/', api_unread_notifications_count, name='api_unread_notifications_count'),
    path('<str:branch>/assigned-animals/', assigned_animals, name='assigned_animals'),
    path('<str:branch>/report-emergency/', report_emergency, name='report_emergency'),
    path('<str:branch>/equipment-log/', equipment_log_view, name='equipment_log_view'),
    path('<str:branch>/support-request/', support_request_view, name='support_request_view'),
    path('dashboard/user/<str:branch>/support-request/', support_request_view, name='user_support_requests'),
]
