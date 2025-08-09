from django.contrib import admin
from core.models import (
    Animal, MedicalRecord, VetTask, EquipmentLog, 
    EmergencyIncident, AnimalLog, DailyActivityReport,
    Notification, Message, SupportTicket, TicketReply,
    SystemLog, Report, Branch
)

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'force_number', 'age', 'owner_name', 'branch', 'created_at']
    list_filter = ['species', 'breed', 'branch', 'created_at']
    search_fields = ['name', 'force_number', 'owner_name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['assigned_users']

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['animal', 'veterinarian', 'report_type', 'diagnosis', 'date_recorded']
    list_filter = ['report_type', 'date_recorded', 'veterinarian']
    search_fields = ['animal__name', 'diagnosis', 'treatment']
    readonly_fields = ['date_recorded', 'updated_at']
    raw_id_fields = ['animal', 'veterinarian']

@admin.register(VetTask)
class VetTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'animal', 'assigned_by', 'assigned_to', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['priority', 'status', 'branch', 'created_at']
    search_fields = ['title', 'description', 'animal__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['animal', 'assigned_by', 'assigned_to']

@admin.register(EquipmentLog)
class EquipmentLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'equipment', 'action', 'timestamp']
    list_filter = ['equipment', 'action', 'timestamp']
    search_fields = ['user__username', 'notes']
    readonly_fields = ['timestamp']

@admin.register(EmergencyIncident)
class EmergencyIncidentAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'animal', 'incident_type', 'severity', 'resolved', 'date_reported']
    list_filter = ['incident_type', 'severity', 'resolved', 'date_reported']
    search_fields = ['description', 'location', 'animal__name']
    readonly_fields = ['date_reported', 'resolved_at']
    raw_id_fields = ['reporter', 'animal', 'resolved_by']

@admin.register(AnimalLog)
class AnimalLogAdmin(admin.ModelAdmin):
    list_display = ['animal', 'user', 'activity_type', 'date']
    list_filter = ['activity_type', 'date']
    search_fields = ['animal__name', 'user__username', 'notes']
    readonly_fields = ['date']
    raw_id_fields = ['user', 'animal']

@admin.register(DailyActivityReport)
class DailyActivityReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'branch', 'date', 'hours_worked', 'created_at']
    list_filter = ['branch', 'date', 'created_at']
    search_fields = ['user__username', 'summary']
    readonly_fields = ['created_at']
    filter_horizontal = ['animals_cared_for']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'subject', 'is_read', 'is_archived', 'timestamp']
    list_filter = ['is_read', 'is_archived', 'is_deleted', 'timestamp']
    search_fields = ['sender__username', 'receiver__username', 'subject', 'content']
    readonly_fields = ['timestamp']
    raw_id_fields = ['sender', 'receiver', 'parent']

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_by', 'assigned_to', 'branch', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'branch', 'created_at']
    search_fields = ['subject', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['created_by', 'assigned_to']

@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'replied_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['ticket__subject', 'replied_by__username', 'message']
    readonly_fields = ['created_at']
    raw_id_fields = ['ticket', 'replied_by']

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'branch', 'action', 'timestamp']
    list_filter = ['role', 'branch', 'action', 'timestamp']
    search_fields = ['user__username', 'message']
    readonly_fields = ['timestamp']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'created_by', 'branch', 'date_created']
    list_filter = ['report_type', 'branch', 'date_created']
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['date_created']
    raw_id_fields = ['created_by']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'location']
