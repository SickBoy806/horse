# All models have been consolidated into core.models
# Import the models from core instead of defining them here

from core.models import (
    Animal, MedicalRecord, VetTask, EquipmentLog, 
    EmergencyIncident, AnimalLog, DailyActivityReport
)

# For backward compatibility, you can still import these models from this module
__all__ = [
    'Animal', 'MedicalRecord', 'VetTask', 'EquipmentLog', 
    'EmergencyIncident', 'AnimalLog', 'DailyActivityReport'
]
