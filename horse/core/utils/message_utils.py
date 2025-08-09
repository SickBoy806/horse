from django.db.models import Q
from core.models import Message

def get_message_thread(message):
    return Message.objects.filter(
        Q(id=message.id) |
        Q(parent=message) |
        Q(id=message.parent_id) if message.parent_id else Q()
    ).order_by('timestamp')

def get_unread_messages_count(user, branch):
    return Message.objects.filter(
        receiver=user,
        branch=branch,
        is_read=False,
        is_deleted=False
    ).count()