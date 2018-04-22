from django.contrib import admin
from accounts.models import User
from tickets.models import Ticket
from tickets.admin import OurActionsOnlyMixin


class TicketInline(OurActionsOnlyMixin, admin.TabularInline):
    model = Ticket

    fields = readonly_fields = ('ticket_id', 'rate', 'sat', 'sun', 'mon', 'tue', 'wed')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ('name', 'email_addr', 'last_login', 'is_contributor',
              'is_organiser', 'is_staff', 'is_active', 'is_superuser',
              'groups', 'user_permissions', 'accessibility_reqs',
              'childcare_reqs', 'dietary_reqs')
    readonly_fields = ('last_login', 'email_addr', 'name',
                       'accessibility_reqs', 'childcare_reqs', 'dietary_reqs')

    inlines = [
        TicketInline,
    ]
