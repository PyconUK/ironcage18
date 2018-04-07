from collections import defaultdict
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string

from ironcage.utils import Scrambler

from .constants import DAYS
from . import prices


class Order(models.Model):
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    billing_name = models.CharField(max_length=200, null=True)
    billing_addr = models.TextField(null=True)
    invoice_number = models.IntegerField(null=True, unique=True)
    status = models.CharField(max_length=10)
    stripe_charge_id = models.CharField(max_length=80)
    stripe_charge_created = models.DateTimeField(null=True)
    stripe_charge_failure_reason = models.CharField(max_length=400, blank=True)
    unconfirmed_details = JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(1000)

    class Manager(models.Manager):
        def get_by_order_id_or_404(self, order_id):
            id = self.model.id_scrambler.backward(order_id)
            return get_object_or_404(self.model, pk=id)

        def create_pending(self, purchaser, billing_details, rate, days_for_self=None, email_addrs_and_days_for_others=None):
            assert days_for_self is not None or email_addrs_and_days_for_others is not None

            billing_name = billing_details['name']
            billing_addr = billing_details['addr']

            unconfirmed_details = {
                'rate': rate,
                'days_for_self': days_for_self,
                'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
            }

            return self.create(
                purchaser=purchaser,
                billing_name=billing_name,
                billing_addr=billing_addr,
                status='pending',
                unconfirmed_details=unconfirmed_details,
            )

    objects = Manager()

    def __str__(self):
        return self.order_id

    @property
    def order_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('tickets:order', args=[self.order_id])

    def update(self, billing_details, rate, days_for_self=None, email_addrs_and_days_for_others=None):
        assert self.payment_required()
        assert days_for_self is not None or email_addrs_and_days_for_others is not None

        self.billing_name = billing_details['name']
        self.billing_addr = billing_details['addr']
        self.unconfirmed_details = {
            'rate': rate,
            'days_for_self': days_for_self,
            'email_addrs_and_days_for_others': email_addrs_and_days_for_others,
        }
        self.save()

    def confirm(self, charge_id, charge_created):
        assert self.payment_required()

        for row in self.build_order_rows():
            row.save()

        self.stripe_charge_id = charge_id
        self.stripe_charge_created = datetime.fromtimestamp(charge_created, tz=timezone.utc)
        self.stripe_charge_failure_reason = ''
        self.status = 'successful'
        self.invoice_number = self.get_next_invoice_number()

        self.save()

    @classmethod
    def get_next_invoice_number(cls):
        prev_invoice_number = cls.objects.aggregate(n=Max('invoice_number'))['n'] or 0
        return prev_invoice_number + 1

    def mark_as_failed(self, charge_failure_reason):
        self.stripe_charge_failure_reason = charge_failure_reason
        self.status = 'failed'

        self.save()

    def mark_as_errored_after_charge(self, charge_id):
        self.stripe_charge_id = charge_id
        self.stripe_charge_failure_reason = ''
        self.status = 'errored'
        self.invoice_number = None

        self.save()

    def build_order_rows(self):
        assert self.payment_required()

        rows = []

        days_for_self = self.unconfirmed_details['days_for_self']
        if days_for_self is not None:
            ticket = Ticket.objects.build(
                rate=self.unconfirmed_details['rate'],
                owner=self.purchaser,
                days=days_for_self,
            )
            row = self.order_rows.build_for_ticket(ticket)
            rows.append(row)

        email_addrs_and_days_for_others = self.unconfirmed_details['email_addrs_and_days_for_others']
        if email_addrs_and_days_for_others is not None:
            for email_addr, days in email_addrs_and_days_for_others:
                ticket = Ticket.objects.build(
                    rate=self.unconfirmed_details['rate'],
                    email_addr=email_addr,
                    days=days,
                )
                rows.append(self.order_rows.build_for_ticket(ticket))

        return rows

    def all_order_rows(self):
        if self.payment_required():
            return self.build_order_rows()
        else:
            return self.order_rows.select_related('ticket').order_by('ticket')

    def all_tickets(self):
        return [order_row.ticket for order_row in self.all_order_rows()]

    def ticket_summary(self):
        num_tickets_by_num_days = defaultdict(int)

        for ticket in self.all_tickets():
            num_tickets_by_num_days[ticket.num_days()] += 1

        summary = []

        for ix in range(5):
            num_days = ix + 1
            if num_tickets_by_num_days[num_days]:
                num_tickets = num_tickets_by_num_days[num_days]
                summary.append({
                    'num_days': num_days,
                    'num_tickets': num_tickets,
                    'per_item_cost_excl_vat': prices.cost_excl_vat(self.rate, num_days),
                    'per_item_cost_incl_vat': prices.cost_incl_vat(self.rate, num_days),
                    'total_cost_excl_vat': prices.cost_excl_vat(self.rate, num_days) * num_tickets,
                    'total_cost_incl_vat': prices.cost_incl_vat(self.rate, num_days) * num_tickets,
                })

        return summary

    def brief_summary(self):
        summary = f'{self.num_tickets()} {self.rate}-rate ticket'
        if self.num_tickets() > 1:
            summary += 's'
        return summary

    @property
    def rate(self):
        # TODO remove this once we can accept multiple rates per order.
        return self.unconfirmed_details['rate']

    @property
    def cost_excl_vat(self):
        return sum(ticket.cost_excl_vat for ticket in self.all_tickets())

    @property
    def cost_incl_vat(self):
        return sum(ticket.cost_incl_vat for ticket in self.all_tickets())

    @property
    def vat(self):
        return self.cost_incl_vat - self.cost_excl_vat

    @property
    def cost_pence_incl_vat(self):
        return 100 * self.cost_incl_vat

    @property
    def full_invoice_number(self):
        return f'S-2018-{self.invoice_number:04d}'

    def num_tickets(self):
        return len(self.all_tickets())

    def unclaimed_tickets(self):
        return [ticket for ticket in self.all_tickets() if ticket.owner is None]

    def ticket_for_self(self):
        tickets = [ticket for ticket in self.all_tickets() if ticket.owner == self.purchaser]
        if len(tickets) == 0:
            return None
        elif len(tickets) == 1:
            return tickets[0]
        else:  # pragma: no cover
            assert False

    def tickets_for_others(self):
        return [ticket for ticket in self.all_tickets() if ticket.owner != self.purchaser]

    def payment_required(self):
        return self.status in ['pending', 'failed']

    def billing_addr_formatted(self):
        lines = [line.strip(',') for line in self.billing_addr.splitlines() if line]
        return ', '.join(lines)


class OrderRow(models.Model):
    order = models.ForeignKey('Order', related_name='order_rows', on_delete=models.CASCADE)
    cost_excl_vat = models.IntegerField()
    ticket = models.OneToOneField('Ticket', related_name='order_row', on_delete=models.DO_NOTHING)
    item_descr = models.CharField(max_length=400)
    item_descr_extra = models.CharField(max_length=400, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Manager(models.Manager):
        def build_for_ticket(self, ticket):
            return self.model(
                order=self.instance,
                cost_excl_vat=ticket.cost_excl_vat,
                ticket=ticket,
                item_descr=ticket.descr_for_order,
                item_descr_extra=ticket.descr_extra_for_order,
            )

    objects = Manager()

    def save(self):
        self.ticket.save()
        self.ticket_id = self.ticket.id
        super().save()

    @property
    def cost_incl_vat(self):
        return int(self.cost_excl_vat * 1.2)

    @property
    def owner_name(self):
        ticket = self.ticket

        if ticket.pk:
            if ticket.owner:
                return ticket.owner.name
            else:
                return ticket.invitation().email_addr
        else:
            if ticket.owner:
                return ticket.owner.name
            else:
                return ticket.email_addr


class Ticket(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    rate = models.CharField(max_length=40)
    thu = models.BooleanField()
    fri = models.BooleanField()
    sat = models.BooleanField()
    sun = models.BooleanField()
    mon = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(2000)

    class Manager(models.Manager):
        def get_by_ticket_id_or_404(self, ticket_id):
            id = self.model.id_scrambler.backward(ticket_id)
            return get_object_or_404(self.model, pk=id)

        def build(self, rate, days, owner=None, email_addr=None):
            assert bool(owner) ^ bool(email_addr)
            day_fields = {day: (day in days) for day in DAYS}
            ticket = self.model(rate=rate, owner=owner, **day_fields)

            if email_addr is not None:
                ticket.email_addr = email_addr

            return ticket

    objects = Manager()

    def __str__(self):
        return self.ticket_id

    @property
    def ticket_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def save(self):
        super().save()
        if hasattr(self, 'email_addr'):
            self.invitations.create(email_addr=self.email_addr)

    def get_absolute_url(self):
        return reverse('tickets:ticket', args=[self.ticket_id])

    def days(self):
        return [DAYS[day] for day in DAYS if getattr(self, day)]

    def num_days(self):
        return len(self.days())

    def ticket_holder_name(self):
        # TODO this is a mess
        if self.owner:
            return self.owner.name
        elif self.pk:
            return self.invitation().email_addr
        else:
            return self.email_addr

    @property
    def descr_for_order(self):
        return f'{self.num_days()}-day {self.rate}-rate ticket'

    @property
    def descr_extra_for_order(self):
        return self.days_sentence

    @property
    def days_sentence(self):
        return ', '.join(self.days())

    @property
    def order(self):
        try:
            return self.order_row.order
        except:
            return None

    @property
    def cost_excl_vat(self):
        try:
            return self.order_row.cost_excl_vat
        except OrderRow.DoesNotExist:
            return prices.cost_excl_vat(self.rate, self.num_days())

    @property
    def cost_incl_vat(self):
        return int(self.cost_excl_vat * 1.2)

    def invitation(self):
        # This will raise an exception if a ticket has multiple invitations
        return self.invitations.get()


class TicketInvitation(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='invitations', on_delete=models.CASCADE)  # TODO make this a OneToOneField
    email_addr = models.EmailField(unique=True)
    token = models.CharField(max_length=12, unique=True)  # An index is automatically created since unique=True
    status = models.CharField(max_length=10, default='unclaimed')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Manager(models.Manager):
        def create(self, **kwargs):
            token = get_random_string(length=12)
            return super().create(token=token, **kwargs)

    objects = Manager()

    def get_absolute_url(self):
        return reverse('tickets:ticket_invitation', args=[self.token])

    def claim_for_owner(self, owner):
        # This would fail if owner already has a ticket, as Ticket.owner is a
        # OneToOneField.
        assert self.status == 'unclaimed'
        ticket = self.ticket
        ticket.owner = owner
        ticket.save()
        self.status = 'claimed'
        self.save()
