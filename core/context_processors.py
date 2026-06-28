from core.models import Notification, Message


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    count = (
        Notification.objects.filter(user=request.user, is_read=False).count()
        + Message.objects.filter(receiver=request.user, is_read=False).count()
    )
    return {'unread_notifications_count': count}
