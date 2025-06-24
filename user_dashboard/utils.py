from .models import UserNotification

def send_notification(user, message, link=None):
    UserNotification.objects.create(user=user, message=message, link=link)