from django.urls import path
from .views import (
    vet_dashboard,
    add_medical_record,
    medical_records_list,
    assign_task,
    vet_task_list,
    vet_task_detail,
)


urlpatterns = [
    path('<str:branch>/', vet_dashboard, name='vet_dashboard'),
    path('<str:branch>/add-record/', add_medical_record, name='add_medical_record'),
    path('<str:branch>/records/', medical_records_list, name='medical_records_list'),
    path('<str:branch>/assign-task/', assign_task, name='assign_task'),
    path('<str:branch>/tasks/', vet_task_list, name='vet_task_list'),
    path('<str:branch>/task/<int:task_id>/', vet_task_detail, name='vet_task_detail'),
]
