from django.contrib.auth import get_user_model
from .models import SystemLog, Notification
from django.utils import timezone

User = get_user_model()

def log_action(user, action, message, ip_address=None):
    """
    Log user actions to the system log
    """
    SystemLog.objects.create(
        user=user,
        role=user.role,
        branch=user.branch,
        action=action,
        message=message,
        ip_address=ip_address
    )

def normalize_branch_name(name):
    """
    Normalize branch names by:
    - Stripping whitespace
    - Lowercasing
    - Removing spaces and underscores
    """
    if not name:
        return ""
    return name.strip().lower().replace("_", "").replace(" ", "")


def create_notification(user, notification_type, title, message, link=None):
    """
    Create a notification for a user
    """
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )

def notify_users(users, notification_type, title, message, link=None):
    """
    Create notifications for multiple users
    """
    notifications = []
    for user in users:
        notifications.append(
            Notification(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link
            )
        )
    Notification.objects.bulk_create(notifications)

def get_user_notifications(user, unread_only=False):
    """
    Get notifications for a user
    """
    notifications = user.notifications.all()
    if unread_only:
        notifications = notifications.filter(is_read=False)
    return notifications.order_by('-created_at')

def mark_notification_read(notification_id, user):
    """
    Mark a notification as read
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False

def get_branch_users(branch, roles=None):
    """
    Get users from a specific branch, optionally filtered by roles
    """
    users = User.objects.filter(branch=branch)
    if roles:
        users = users.filter(role__in=roles)
    return users

def get_user_dashboard_url(user):
    """
    Get the appropriate dashboard URL for a user based on their role
    """
    branch_name = user.branch.name if user.branch else 'default'
    
    role_urls = {
        'superadmin': '/dashboard/',
        'admin': f'/dashboard/admin/{branch_name}/',
        'veterinarian': f'/dashboard/vet/{branch_name}/',
        'staff': f'/dashboard/staff/{branch_name}/',
        'user': f'/dashboard/user/{branch_name}/',
    }
    
    return role_urls.get(user.role, '/dashboard/')

def can_access_branch(user, branch_name):
    """
    Check if a user can access a specific branch
    """
    if user.role == 'superadmin':
        return True
    
    if user.branch and user.branch.name.lower() == branch_name.lower():
        return True
    
    return False

def get_user_permissions(user):
    """
    Get permissions for a user based on their role
    """
    permissions = {
        'can_create_users': False,
        'can_assign_tasks': False,
        'can_view_all_animals': False,
        'can_create_medical_records': False,
        'can_manage_support_tickets': False,
        'can_view_system_logs': False,
        'can_generate_reports': False,
    }
    
    if user.role == 'superadmin':
        # Superadmin has all permissions
        for key in permissions:
            permissions[key] = True
    elif user.role == 'admin':
        permissions.update({
            'can_create_users': True,
            'can_assign_tasks': True,
            'can_view_all_animals': True,
            'can_manage_support_tickets': True,
            'can_generate_reports': True,
        })
    elif user.role == 'veterinarian':
        permissions.update({
            'can_assign_tasks': True,
            'can_create_medical_records': True,
            'can_view_all_animals': True,
            'can_generate_reports': True,
        })
    elif user.role == 'staff':
        permissions.update({
            'can_view_all_animals': True,
        })
    # 'user' role keeps default permissions (all False)
    
    return permissions
