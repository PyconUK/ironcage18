from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand

GROUPS = {
    'Staff': [
        ('change_user', 'accounts', 'user'),
        ('change_proposal', 'cfp', 'proposal'),
        ('change_application', 'grants', 'application'),
        ('change_orderrow', 'orders', 'orderrow'),
        ('change_ticket', 'tickets', 'ticket'),
    ]
}


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for group_name in GROUPS:
            group_obj, created = Group.objects.get_or_create(name=group_name)

            for permission in GROUPS[group_name]:
                perm_obj = Permission.objects.get_by_natural_key(*permission)

                group_obj.permissions.add(perm_obj)
