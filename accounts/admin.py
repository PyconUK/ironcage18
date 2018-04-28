from django.contrib import admin
from accounts.models import User
from tickets.models import Ticket
from ironcage.admin import OurActionsOnlyMixin


class TicketInline(OurActionsOnlyMixin, admin.TabularInline):
    model = Ticket

    fields = readonly_fields = ('ticket_id', 'rate', 'sat', 'sun', 'mon', 'tue', 'wed')


@admin.register(User)
class UserAdmin(OurActionsOnlyMixin, admin.ModelAdmin):

    inlines = [
        TicketInline,
    ]

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['name', 'email_addr', 'last_login', 'is_contributor',
                    'is_organiser', 'is_staff', 'is_active', 'is_superuser',
                    'groups', 'user_permissions', 'accessibility_reqs',
                    'childcare_reqs', 'dietary_reqs']
        else:
            return ['name', 'is_contributor', 'is_organiser']

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['last_login', 'email_addr', 'name', 'accessibility_reqs',
                    'childcare_reqs', 'dietary_reqs']
        else:
            return self.get_fields(request, obj)

    def get_list_display(self, request):

        if request.user.is_superuser:
            fields = ['user_id', 'name', 'email_addr', 'is_staff',
                      'is_contributor', 'is_organiser']

            long_fields = ['accessibility_reqs', 'childcare_reqs', 'dietary_reqs']

            for field in long_fields:
                if request.GET.get(field):
                    fields.append(field)

            return fields
        else:
            return ['user_id', 'name', 'is_contributor', 'is_organiser']

    def get_list_filter(self, request):

        if request.user.is_superuser:
            return ['is_contributor', 'is_organiser', 'is_staff',
                    'accessibility_reqs', 'childcare_reqs', 'dietary_reqs']
        else:
            return ['is_contributor', 'is_organiser']
