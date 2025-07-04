from django.contrib.auth.decorators import permission_required
from django.urls import path
from .views import (superadmin_dashboard ,superadmin_manage_branches,
                    superadmin_manage_users, superadmin_view_logs,
                    superadmin_analytics, superadmin_tickets, manage_branches,add_branch,
                    edit_branch, delete_branch,superadmin_user_add,superadmin_user_edit,superadmin_user_delete,
                    superadmin_permissions,promote_to_vet,lock_account,unlock_account)

urlpatterns = [
    path('', superadmin_dashboard, name='superadmin_dashboard'),
# SuperAdmin Feature Routes
    path('branches/', superadmin_manage_branches, name='superadmin_manage_branches'),
    path('users/', superadmin_manage_users, name='superadmin_manage_users'),
    path('logs/', superadmin_view_logs, name='superadmin_view_logs'),
    path('analytics/', superadmin_analytics, name='superadmin_analytics'),
    path('tickets/', superadmin_tickets, name='superadmin_tickets'),
    path('', superadmin_dashboard, name='superadmin_dashboard'),
    path('branches/', manage_branches, name='superadmin_manage_branches'),
    path('branches/add/', add_branch, name='superadmin_add_branch'),
    path('branches/edit/<int:branch_id>/', edit_branch, name='superadmin_edit_branch'),
    path('branches/delete/<int:branch_id>/', delete_branch, name='superadmin_delete_branch'),
    path('users/add/', superadmin_user_add, name='superadmin_user_add'),
    path('users/edit/<int:user_id>/', superadmin_user_edit, name='superadmin_user_edit'),
    path('users/delete/<int:user_id>/', superadmin_user_delete, name='superadmin_user_delete'),
    path('superadmin_permissions/', superadmin_permissions, name='superadmin_permissions'),
    path('promote/<int:user_id>/', promote_to_vet, name='promote_to_vet'),
    path('lock/<int:user_id>/', lock_account, name='lock_account'),
    path('unlock/<int:user_id>/', unlock_account, name='unlock_account'),

]
