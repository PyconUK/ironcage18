from django.contrib import admin
from schedule.models import Room, Session, Stream
from ironcage.admin import OurActionsOnlyMixin
from import_export.admin import ImportMixin, ExportMixin


# admin.site.register(Room)
admin.site.register(Session)
# admin.site.register(Stream)


@admin.register(Room)
class RoomAdmin(ExportMixin, admin.ModelAdmin):
    pass


@admin.register(Stream)
class StreamAdmin(ImportMixin, admin.ModelAdmin):
    pass
