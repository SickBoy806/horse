
from .models import SystemLog

def log_action(user, action, message):
    SystemLog.objects.create(
        user=user,
        role=user.role,
        branch=user.branch,
        action=action,
        message=message
    )
