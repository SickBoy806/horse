# All models have been consolidated into core.models
# Import the models from core instead of defining them here

from core.models import (
    VetTask, MedicalRecord, Animal, AnimalLog, 
    DailyActivityReport, EmergencyIncident
)

# For backward compatibility, you can still import these models from this module
__all__ = [
    'VetTask', 'MedicalRecord', 'Animal', 'AnimalLog', 
    'DailyActivityReport', 'EmergencyIncident'
]
