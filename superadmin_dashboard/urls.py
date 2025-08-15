from django.urls import path

# SuperAdmin-only views
from .views import (
    superadmin_dashboard,
    superadmin_manage_branches,
    superadmin_manage_users,
    superadmin_view_logs,
    superadmin_analytics,
    superadmin_tickets,
    manage_branches,
    add_branch,training_report,
    edit_branch, branch_animal_report,
    delete_branch,branch_support_report,
    superadmin_user_add,branch_task_report,
    superadmin_user_edit, branch_equipment_report,
    superadmin_user_delete,branch_medical_report,
    superadmin_permissions, superadmin_task_logs,
    promote_to_vet, superadmin_branch_tasks,
    lock_account, superadmin_completed_tasks,
    superadmin_create_task,
    unlock_account,superadmin_pending_tasks
)

# Global messaging views from core
from core.views import (
    inbox,
    compose_message,
    message_detail,
    reply_message
)

urlpatterns = [
    # Dashboard
    path('', superadmin_dashboard, name='superadmin_dashboard'),

    # Branch management
    path('branches/', superadmin_manage_branches, name='superadmin_manage_branches'),
    path('branches/manage/', manage_branches, name='superadmin_manage_branches_alt'),  # alternative internal view
    path('branches/add/', add_branch, name='superadmin_add_branch'),
    path('branches/edit/<int:branch_id>/', edit_branch, name='superadmin_edit_branch'),
    path('branches/delete/<int:branch_id>/', delete_branch, name='superadmin_delete_branch'),
    path('tasks/create/', superadmin_create_task, name='superadmin_create_task'),
    path('tasks/pending/', superadmin_pending_tasks, name='superadmin_pending_tasks'),
    path('tasks/completed/', superadmin_completed_tasks, name='superadmin_completed_tasks'),
    path('tasks/branches/', superadmin_branch_tasks, name='superadmin_branch_tasks'),
    path('tasks/logs/', superadmin_task_logs, name='superadmin_task_logs'),


    # User management
    path('users/', superadmin_manage_users, name='superadmin_manage_users'),
    path('users/add/', superadmin_user_add, name='superadmin_user_add'),
    path('users/edit/<int:user_id>/', superadmin_user_edit, name='superadmin_user_edit'),
    path('users/delete/<int:user_id>/', superadmin_user_delete, name='superadmin_user_delete'),
    path('users/promote/<int:user_id>/', promote_to_vet, name='promote_to_vet'),
    path('users/lock/<int:user_id>/', lock_account, name='lock_account'),
    path('users/unlock/<int:user_id>/', unlock_account, name='unlock_account'),
    path('permissions/', superadmin_permissions, name='superadmin_permissions'),

    # Logs & Analytics
    path('logs/', superadmin_view_logs, name='superadmin_view_logs'),
    path('analytics/', superadmin_analytics, name='superadmin_analytics'),

    # Tickets
    path('tickets/', superadmin_tickets, name='superadmin_tickets'),

    # Messaging (using global core views but with superadmin-specific names)
    path('messages/inbox/', inbox, name='superadmin_inbox'),
    path('messages/sent/', inbox, name='superadmin_sent_messages'),  # can filter in template
    path('messages/compose/', compose_message, name='superadmin_compose_message'),
    path('messages/<int:message_id>/', message_detail, name='superadmin_message_detail'),
    path('messages/<int:message_id>/reply/', reply_message, name='superadmin_reply_message'),


    # --- Reports ---
    path('reports/medical/', branch_medical_report, name='branch_medical_report'),
    path('reports/equipment/', branch_equipment_report, name='branch_equipment_report'),
    path('reports/tasks/', branch_task_report, name='branch_task_report'),
    path('reports/support/', branch_support_report, name='branch_support_report'),
    path('reports/animals/', branch_animal_report, name='branch_animal_report'),
    path('reports/training/', training_report, name='training_report'),

]
