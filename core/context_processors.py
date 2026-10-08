from core.models import Notification, Message


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    count = (
        Notification.objects.filter(user=request.user, is_read=False).count()
        + Message.objects.filter(receiver=request.user, is_read=False).count()
    )
    return {'unread_notifications_count': count}


_ROLE_BASE_TEMPLATES = {
    'superadmin':   'superadmin_dashboard/base_dashboard.html',
    'admin':        'admin_dashboard/base_admin.html',
    'veterinarian': 'veterinarian_dashboard/base_dashboard.html',
    'staff':        'staff_dashboard/base_staff.html',
}


def role_base(request):
    """Default `base_template`/`branch` so any page can render inside the user's role shell.

    Views that pass their own `base_template` or `branch` override these.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'base_template': 'tpf_public_base.html', 'branch': ''}
    branch = user.branch.name.lower() if getattr(user, 'branch', None) else ''
    role = getattr(user, 'role', None)
    if not branch and role != 'superadmin':
        # Branch-scoped sidebars can't build their links without a branch.
        return {'base_template': 'tpf_public_base.html', 'branch': ''}
    return {
        'base_template': _ROLE_BASE_TEMPLATES.get(role, 'user_dashboard/base_user.html'),
        'branch': branch,
    }
