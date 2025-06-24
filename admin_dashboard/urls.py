from django.urls import path
from . import views
from .views import (
    admin_dashboard,
    create_user,
    assign_task,
    approve_activities,
    animal_list,
    admin_reports,
    user_list,
)

urlpatterns = [
    path('<str:branch>/', admin_dashboard, name='admin_dashboard'),
    path('<str:branch>/create-user/', create_user, name='create_user'),  # 🔁 Fix this line
    path('<str:branch>/assign-task/', assign_task, name='assign_task'),
    path('<str:branch>/approve-activities/', approve_activities, name='approve_activities'),
    path('<str:branch>/animal-list/', animal_list, name='animal_list'),
    path('<str:branch>/admin-reports/', admin_reports, name='admin_reports'),
    path('<str:branch>/user-list/', user_list, name='user_list'),
]

