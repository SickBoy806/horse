from django.urls import path
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
)


urlpatterns = [
    path('<str:branch>/', vet_dashboard, name='vet_dashboard'),
    path('<str:branch>/add-record/', add_medical_record, name='add_medical_record'),
    path('<str:branch>/records/', medical_records_list, name='medical_records_list'),
    path('<str:branch>/assign-task/', assign_task, name='assign_task'),
    path('<str:branch>/tasks/', vet_task_list, name='vet_task_list'),
    path('<str:branch>/task/<int:task_id>/', vet_task_detail, name='vet_task_detail'),
    path('<str:branch>/search-medical-records/', search_medical_records, name='search_medical_records'),
    path('<str:branch>/tasks/pending/', pending_tasks, name='pending_tasks'),
    path('<str:branch>/tasks/completed/', completed_tasks, name='completed_tasks'),
    path('<str:branch>/add-patient/', add_patient, name='add_patient'),
    path('<str:branch>/patients/', patient_list, name='patient_list'),
    path('<str:branch>/search-patients/', search_patients, name='search_patients'),
    path('<str:branch>/analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('<str:branch>/performance-reports/', performance_reports, name='performance_reports'),
    path('<str:branch>/settings/', vet_settings, name='vet_settings'),
    path('<str:branch>/help-support/', help_support, name='help_support'),


    # <--- here
]
