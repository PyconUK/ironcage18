import csv
import io
import random

from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from accounts.models import Badge, User
from accounts.views import assign_a_snake
from extras.models import ExtraItem
from ironcage.emails import send_mail_with_attachment
from tickets.models import Ticket

STANDARD_SNAKES = [
    ('blue', 'deerstalker'),
    ('yellow', 'crown'),
    ('red', 'glasses'),
    ('green', 'dragon'),
    ('purple', 'mortar'),
    ('orange', 'astronaut'),
]

LUNCH_OPTIONS = ['1300', '1330', '1400']


def assign_badges_to_tickets():
    for ticket in Ticket.objects.all():
        if ticket.badge.count() < 1:
            badge = Badge(ticket=ticket)
            badge.save()


def add_spare_badges(number_spare_badges):
    for i in range(number_spare_badges):
        badge = Badge()
        badge.save()


def do_claimed_tickets(output):
    # All claimed ticket holders
    claimed_tickets = Ticket.objects.filter(
        owner__isnull=False
    ).order_by(
        '-sat', '-sun', '-mon', '-tue', '-wed'
    ).all()

    for ticket in claimed_tickets:
        if ticket.owner.badge_snake_colour in [None, ''] or ticket.owner.badge_snake_extras in [None, '']:
            assign_a_snake(ticket.owner)

        user = {
            'name': ticket.owner.name,
            'last_bit_of_name': ticket.owner.name.split(' ')[-1],
            'company': ticket.owner.badge_company,
            'pronoun': ticket.owner.badge_pronoun,
            'twitter': ticket.owner.badge_twitter,
            'snake': ticket.owner.badge_snake_colour,
            'extra': ticket.owner.badge_snake_extras,
            'sat': 1 if ticket.sat else 0,
            'sun': 1 if ticket.sun else 0,
            'mon': 1 if ticket.mon else 0,
            'tue': 1 if ticket.tue else 0,
            'wed': 1 if ticket.wed else 0,
            'ticket_id': ticket.ticket_id,
            'badge_id': ticket.badge.get().badge_id,
            'ukpa': 1 if ticket.owner.is_ukpa_member else 0,
            'type': 'claimed'
        }

        if ticket.owner.is_organiser:
            user['background'] = 'red'
        elif ticket.owner.is_contributor:
            user['background'] = 'blue'
        else:
            user['background'] = 'yellow'

        user['lunch'] = LUNCH_OPTIONS[len(output) % 3]

        output.append(user)


def do_spare_badges(output):
    # All spare badges
    spare_badges = Badge.objects.filter(
        ticket=None
    ).all()

    for i, badge in enumerate(spare_badges):

        colour, extra = random.choice(STANDARD_SNAKES)
        user = {
            'name': '',
            'company': '',
            'pronoun': '',
            'twitter': '',
            'snake': colour,
            'extra': extra,
            'sat': 0,
            'sun': 0,
            'mon': 0,
            'tue': 0,
            'wed': 0,
            'ticket_id': '',
            'badge_id': badge.badge_id,
            'ukpa': 0,
            'type': 'spare'
        }

        if i < (len(spare_badges) / 6):
            user['background'] = 'blue'
        else:
            user['background'] = 'yellow'

        user['lunch'] = LUNCH_OPTIONS[len(output) % 3]

        output.append(user)


def do_childrens_tickets(output):

    children_ticket_content_type = ContentType.objects.get(
        app_label="extras", model="childrenticket"
    )

    # All childrens ticket holders
    childrens_tickets = ExtraItem.objects.filter(
        content_type=children_ticket_content_type
    ).all()

    childrens_tickets = sorted(childrens_tickets, key=lambda x: x.item.name)

    for ticket in childrens_tickets:

        colour, extra = random.choice(STANDARD_SNAKES)

        user = {
            'name': ticket.item.name,
            'company': '',
            'pronoun': '',
            'twitter': '',
            'snake': colour,
            'extra': extra,
            'sat': 0,
            'sun': 0,
            'mon': 0,
            'tue': 0,
            'wed': 0,
            'ticket_id': ticket.item_id,
            'badge_id': '',
            'ukpa': 0,
            'type': 'children',
            'background': 'yellow',
        }

        output.append(user)


class Command(BaseCommand):

    def handle(self, **kwargs):

        fieldnames = [
            'name', 'last_bit_of_name', 'company', 'pronoun', 'twitter', 'snake',
            'extra', 'background', 'sat', 'sun', 'mon', 'tue', 'wed', 'lunch',
            'ticket_id', 'badge_id', 'ukpa', 'type'
        ]

        output = []

        assign_badges_to_tickets()

        number_spare_badges = Badge.objects.filter(ticket=None).count()
        if number_spare_badges < 200:
            add_spare_badges(200 - number_spare_badges)

        do_claimed_tickets(output)
        output = sorted(output, key=lambda x: x['last_bit_of_name'])

        do_childrens_tickets(output)
        do_spare_badges(output)

        f = io.StringIO()

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output)

        f.seek(0)

        send_mail_with_attachment(
            f'Badges',
            'Here is your badge data',
            User.objects.get(pk=1).email_addr,
            [('badges.csv', f.read(), 'text/csv')]
        )
