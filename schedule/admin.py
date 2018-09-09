from django.contrib import admin
from schedule.models import Room, Slot, SlotEvent
from ironcage.admin import OurActionsOnlyMixin
from import_export.admin import ImportExportMixin

admin.site.register(SlotEvent)

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ['room', 'date', 'session_name', 'time', 'duration', 'event_type']


@admin.register(Room)
class RoomAdmin(OurActionsOnlyMixin, ImportExportMixin, admin.ModelAdmin):
    pass
