from django.urls import path
from veterinarian_dashboard.views import vet_animal_list_wrapper
from core.views import (
    add_animal,
    view_animal_detail,
    animal_list,
)

from .views import (
    vet_dashboard,
    add_medical_record,
    medical_records_list,
    assign_task,
    vet_task_list,
    vet_task_detail,
    search_medical_records,
    pending_tasks,
    completed_tasks,
    add_patient,
    patient_list,
    search_patients,
    analytics_dashboard,
    performance_reports,
    vet_settings,
    help_support,
    search_animal_logs,
    animal_logs,
    inbox,
    sent_messages,
    archived_messages,
    deleted_messages,
    compose_message,
    message_detail,
    reply_message,
    send_message,
    notifications_view,
    update_task_view,
    equipment_log_view,
    report_emergency_view,
    support_request_view,
    notification_count_api,
    unread_message_count,
    patient_detail,
)

urlpatterns = [
    # Dashboard
    path('<str:branch>/', vet_dashboard, name='vet_dashboard'),

    # Animals (core views)
    # path('<str:branch>/animals/', animal_list, name='animal_list'),
    path('<str:branch>/animals/add/', add_animal, name='add_animal'),
    path('<str:branch>/animals/<int:animal_id>/', view_animal_detail, name='view_animal_detail'),
    path('<str:branch>/animals/', vet_animal_list_wrapper, name='animal_list'),


    # Animal Logs
    path('<str:branch>/animal-logs/', animal_logs, name='animal_logs'),
    path('<str:branch>/animal-logs/search/', search_animal_logs, name='search_animal_logs'),

    # Medical Records
    path('<str:branch>/records/', medical_records_list, name='medical_records_list'),
    path('<str:branch>/add-record/', add_medical_record, name='add_medical_record'),
    path('<str:branch>/search-medical-records/', search_medical_records, name='search_medical_records'),

    # Tasks
    path('<str:branch>/assign-task/', assign_task, name='assign_task'),
    path('<str:branch>/tasks/', vet_task_list, name='vet_task_list'),
    path('<str:branch>/task/<int:task_id>/', vet_task_detail, name='vet_task_detail'),
    path('<str:branch>/tasks/pending/', pending_tasks, name='pending_tasks'),
    path('<str:branch>/tasks/completed/', completed_tasks, name='completed_tasks'),
    path('<str:branch>/update-task/', update_task_view, name='update_task'),

    # Patients
    path('<str:branch>/add-patient/', add_patient, name='add_patient'),
    path('<str:branch>/patients/', patient_list, name='patient_list'),
    path('<str:branch>/search-patients/', search_patients, name='search_patients'),
    path('<str:branch>/patients/<int:patient_id>/', patient_detail, name='patient_detail'),

    # Messages
    path('<str:branch>/messages/', inbox, name='inbox'),
    path('<str:branch>/messages/sent/', sent_messages, name='sent_messages'),
    path('<str:branch>/messages/archived/', archived_messages, name='archived_messages'),
    path('<str:branch>/messages/deleted/', deleted_messages, name='deleted_messages'),
    path('<str:branch>/messages/compose/', compose_message, name='compose_message'),
    path('<str:branch>/messages/<int:message_id>/', message_detail, name='message_detail'),
    path('<str:branch>/messages/<int:message_id>/reply/', reply_message, name='reply_message'),
    path('<str:branch>/messages/send/', send_message, name='send_message'),

    # Analytics & Reports
    path('<str:branch>/analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('<str:branch>/performance-reports/', performance_reports, name='performance_reports'),

    # Settings & Support
    path('<str:branch>/settings/', vet_settings, name='vet_settings'),
    path('<str:branch>/help-support/', help_support, name='help_support'),
    path('<str:branch>/support-request/', support_request_view, name='support_request'),

    # Notifications
    path('<str:branch>/notifications/', notifications_view, name='notifications'),

    # Equipment logs & emergencies
    path('<str:branch>/equipment-logs/', equipment_log_view, name='equipment_logs'),
    path('<str:branch>/report-emergency/', report_emergency_view, name='report_emergency'),

    # APIs (non-branch scoped)
    path('api/notifications/count/', notification_count_api, name='notification_count_api'),
    path('api/unread-messages/', unread_message_count, name='unread_message_count'),
]
