from django.contrib import admin
from schedule.models import Room, Session, Stream
from ironcage.admin import OurActionsOnlyMixin
from import_export.admin import ImportMixin, ImportExportMixin

admin.site.register(Session)


@admin.register(Room)
class RoomAdmin(OurActionsOnlyMixin, ImportExportMixin, admin.ModelAdmin):
    pass


@admin.register(Stream)
class StreamAdmin(OurActionsOnlyMixin, ImportMixin, admin.ModelAdmin):
    pass
