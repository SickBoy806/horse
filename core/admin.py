from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import SupportTicket, TicketReply
from .models import SystemLog

# admin.site.register(SupportTicket)
# admin.site.register(TicketReply)
# admin.site.register(SystemLog)



from .models import Deployment, DeploymentTeam, DeploymentFind, AnimalStatusChange  # noqa: E402


class DeploymentTeamInline(admin.TabularInline):
    model = DeploymentTeam
    extra = 0


class DeploymentFindInline(admin.TabularInline):
    model = DeploymentFind
    extra = 0


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'deployment_type', 'branch', 'started_at', 'status', 'outcome', 'arrests')
    list_filter = ('status', 'outcome', 'deployment_type', 'branch')
    search_fields = ('reference', 'location', 'ob_number', 'requested_by')
    date_hierarchy = 'started_at'
    inlines = [DeploymentTeamInline, DeploymentFindInline]


@admin.register(AnimalStatusChange)
class AnimalStatusChangeAdmin(admin.ModelAdmin):
    list_display = ('animal', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status',)

from .models import Certification, HandlerAssignment  # noqa: E402


@admin.register(HandlerAssignment)
class HandlerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('animal', 'handler', 'role', 'start_date', 'end_date')
    list_filter = ('role', 'animal__branch')
    search_fields = ('animal__name', 'animal__force_number', 'handler__username')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('animal', 'cert_type', 'certificate_number', 'issued_date', 'expiry_date', 'handler')
    list_filter = ('cert_type', 'animal__branch')
    search_fields = ('animal__name', 'certificate_number')
    date_hierarchy = 'expiry_date'


from .models import HoofCareRecord, HousingAssignment, HousingUnit, TackItem  # noqa: E402


@admin.register(HoofCareRecord)
class HoofCareRecordAdmin(admin.ModelAdmin):
    list_display = ('animal', 'date', 'service', 'farrier', 'condition', 'next_due')
    list_filter = ('service', 'condition', 'animal__branch')
    search_fields = ('animal__name', 'farrier')
    date_hierarchy = 'date'


@admin.register(TackItem)
class TackItemAdmin(admin.ModelAdmin):
    list_display = ('item_type', 'asset_tag', 'branch', 'assigned_horse', 'condition', 'last_inspected', 'is_active')
    list_filter = ('item_type', 'condition', 'is_active', 'branch')
    search_fields = ('asset_tag', 'description', 'assigned_horse__name')


class HousingAssignmentInline(admin.TabularInline):
    model = HousingAssignment
    extra = 0


@admin.register(HousingUnit)
class HousingUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'branch', 'capacity', 'is_active')
    list_filter = ('kind', 'branch', 'is_active')
    inlines = [HousingAssignmentInline]


from .models import StockItem, StockMovement  # noqa: E402


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    fields = ('date', 'kind', 'quantity', 'animal', 'batch_number', 'expiry_date', 'reference', 'recorded_by')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'branch', 'unit', 'reorder_level', 'is_active')
    list_filter = ('category', 'branch', 'is_active')
    search_fields = ('name', 'supplier')
    inlines = [StockMovementInline]
