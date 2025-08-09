# All models have been consolidated into core.models
# Import the models from core instead of defining them here

from core.models import (
    AnimalLog, DailyActivityReport, Message, Notification,
    EmergencyIncident, EquipmentLog, SupportTicket
)

# For backward compatibility, you can still import these models from this module
__all__ = [
    'AnimalLog', 'DailyActivityReport', 'Message', 'Notification',
    'EmergencyIncident', 'EquipmentLog', 'SupportTicket'
]

# Legacy model names for backward compatibility
UserMessage = Message
UserNotification = Notification
SupportRequest = SupportTicket
