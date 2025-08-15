from django.urls import path
from . import views
from .views import notifications
from .views import (
    admin_dashboard,
    create_user,
    task_assign,
    approve_activities,
    animal_list,
    admin_user_list,
    user_delete,
    user_edit,
    task_list,
    task_detail,
    admin_incident_logs,
    admin_care_logs,
    admin_reports,
    admin_support,
    admin_animals,
    support_ticket_list,
    support_ticket_detail,
    close_support_ticket,
    notifications,
)

urlpatterns = [
    path('<str:branch>/', admin_dashboard, name='admin_dashboard'),
    path('<str:branch>/create-user/', create_user, name='create_user'),  # 🔁 Fix this line
    path('<str:branch>/task_assign/', task_assign, name='task_assign'),
    path('<str:branch>/approve-activities/', approve_activities, name='approve_activities'),
    path('<str:branch>/animal-list/', animal_list, name='animal_list'),
    path('<str:branch>/admin-reports/', admin_reports, name='admin_reports'),
    path('<str:branch>/admin_user_list/', admin_user_list, name='admin_user_list'),
    path('<str:branch>/tasks/', task_list, name='admin_task_list'),
    path('<str:branch>/tasks/assign/', task_assign, name='admin_task_assign'),
    path('<str:branch>/tasks/<int:task_id>/', task_detail, name='admin_task_detail'),
    path('<str:branch>/admin_reports/<int:task_id>/', admin_reports, name='admin_reports'),
    path('<str:branch>/admin_care_logs/', admin_care_logs, name='admin_care_logs'),
    path('<str:branch>/admin_incident_logs/', admin_incident_logs, name='admin_incident_logs'),
    path('<str:branch>/admin_animals/', admin_animals, name='admin_animals'),
    path('<str:branch>/admin_support/', admin_support, name='admin_support'),
    path('<str:branch>/support/', support_ticket_list, name='admin_support'),
    path('<str:branch>/support/<int:ticket_id>/', support_ticket_detail, name='admin_support_detail'),
    path('<str:branch>/support/<int:ticket_id>/close/', close_support_ticket, name='admin_support_close'),
    path('<str:branch>/create-user/', views.user_add, name='admin_user_add'),
    path('<str:branch>/user_edit/<int:user_id>/', user_edit, name='admin_user_edit'),
    path('<str:branch>/user_delete/<int:user_id>/', user_delete, name='admin_user_delete'),
    path('dashboard/vet/<branch>/notifications/', notifications, name='notifications'),
    path('dashboard/admin/<str:branch>/medical-records/', views.admin_medical_records, name='medical_records'),
    path('<str:branch>/equipment-logs/', views.admin_equipment_logs, name='admin_equipment_logs'),



]





