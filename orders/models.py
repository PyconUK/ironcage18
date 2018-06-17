from collections import Counter
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ironcage.utils import Scrambler
from tickets.models import Ticket


class SalesRecord:
    '''Mixin for behaviour common to Order and Refund'''

    @property
    def cost_excl_vat(self):
        return sum(row.cost_excl_vat for row in self.all_order_rows())

    @property
    def cost_incl_vat(self):
        return sum(row.cost_incl_vat for row in self.all_order_rows())

    @property
    def vat(self):
        return self.cost_incl_vat - self.cost_excl_vat

    def order_rows_summary(self):
        row_counts = Counter()

        for row in self.all_order_rows():
            row_counts[(row.item_descr, row.cost_excl_vat, row.cost_incl_vat)] += 1

        summary = []

        for (item_descr, cost_excl_vat, cost_incl_vat), count in row_counts.items():
            summary.append({
                'item_descr': item_descr,
                'quantity': count,
                'per_item_cost_excl_vat': cost_excl_vat,
                'per_item_cost_incl_vat': cost_incl_vat,
                'total_cost_excl_vat': cost_excl_vat * count,
                'total_cost_incl_vat': cost_incl_vat * count,
            })

        return sorted(summary, key=lambda record: record['total_cost_excl_vat'], reverse=True)

    def brief_summary(self):
        summary = self.order_rows_summary()
        return ', '.join(f'{record["quantity"]} × {record["item_descr"]}' for record in summary)

    def billing_addr_formatted(self):
        lines = [line.strip(',') for line in self.billing_addr.splitlines() if line]
        return ', '.join(lines)


class Order(models.Model, SalesRecord):
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    billing_name = models.CharField(max_length=200, null=True)
    billing_addr = models.TextField(null=True)
    invoice_number = models.IntegerField(null=True, unique=True)
    status = models.CharField(max_length=10)
    stripe_charge_id = models.CharField(max_length=80)
    stripe_charge_created = models.DateTimeField(null=True)
    stripe_charge_failure_reason = models.CharField(max_length=400, blank=True)
    unconfirmed_details = JSONField()
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(1000)

    class Manager(models.Manager):
        def get_by_order_id_or_404(self, order_id):
            id = self.model.id_scrambler.backward(order_id)
            return get_object_or_404(self.model, pk=id)

        def create_pending(self, purchaser, billing_details, rate, days_for_self=None, email_addrs_and_days_for_others=None):
            if self.content_type == ContentType.objects.get(app_label="tickets", model="ticket"):
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
        return reverse('orders:order', args=[self.order_id])

    @property
    def refunds(self):
        row_ids = [row.id for row in self.all_order_rows()]
        return Refund.objects.filter(order_rows__id__in=row_ids)

    def update(self, billing_details, rate, days_for_self=None, email_addrs_and_days_for_others=None):
        assert self.payment_required()

        if self.content_type == ContentType.objects.get(app_label="tickets", model="ticket"):
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

    @property
    def cost_pence_incl_vat(self):
        return 100 * self.cost_incl_vat

    @property
    def full_invoice_number(self):
        return f'S-2018-{self.invoice_number:04d}'

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

        if self.content_type == ContentType.objects.get(app_label="tickets", model="ticket"):

            days_for_self = self.unconfirmed_details['days_for_self']
            if days_for_self is not None:
                ticket = Ticket.objects.build(
                    rate=self.unconfirmed_details['rate'],
                    owner=self.purchaser,
                    days=days_for_self,
                )
                row = self.order_rows.build_for_item(ticket)
                rows.append(row)

            email_addrs_and_days_for_others = self.unconfirmed_details['email_addrs_and_days_for_others']
            if email_addrs_and_days_for_others is not None:
                for email_addr, name, days in email_addrs_and_days_for_others:
                    ticket = Ticket.objects.build(
                        rate=self.unconfirmed_details['rate'],
                        email_addr=email_addr,
                        days=days,
                    )
                    rows.append(self.order_rows.build_for_item(ticket))

        return rows

    def all_order_rows(self):
        if self.payment_required():
            return self.build_order_rows()
        else:
            return self.order_rows.order_by('content_type', 'object_id')

    def all_items(self):
        return [order_row.item for order_row in self.all_order_rows()]

    def all_tickets(self):
        return [item for item in self.all_items() if isinstance(item, Ticket)]

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


class Refund(models.Model, SalesRecord):
    reason = models.CharField(max_length=400)
    credit_note_number = models.IntegerField()
    stripe_refund_id = models.CharField(max_length=80)
    stripe_refund_created = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(5000)

    class Manager(models.Manager):
        def get_by_refund_id_or_404(self, refund_id):
            id = self.model.id_scrambler.backward(refund_id)
            return get_object_or_404(self.model, pk=id)

        def create_for_item(self, item, reason, stripe_refund_id, stripe_refund_created):
            refund = self.create(
                reason=reason,
                stripe_refund_id=stripe_refund_id,
                stripe_refund_created=datetime.fromtimestamp(
                    stripe_refund_created,
                    tz=timezone.utc
                ),
                credit_note_number=0
            )

            order_row = item.order_row
            order_row.object_id = None
            order_row.content_type = None
            order_row.refund = refund
            order_row.save()

            refund.credit_note_number = refund.get_next_credit_note_number()
            refund.save()

            item.delete()
            return refund

    objects = Manager()

    @property
    def refund_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    @property
    def order(self):
        row_ids = [row.id for row in self.all_order_rows()]
        return Order.objects.get(order_rows__id__in=row_ids)

    @property
    def full_credit_note_number(self):
        return f'R-2018-{self.order.invoice_number:04d}-{self.credit_note_number:02d}'

    def get_next_credit_note_number(self):
        return self.order_rows.count()

    def all_order_rows(self):
        return self.order_rows.order_by('content_type', 'object_id')


class OrderRow(models.Model):
    order = models.ForeignKey('Order', related_name='order_rows', on_delete=models.CASCADE)
    refund = models.ForeignKey('Refund', related_name='order_rows', on_delete=models.DO_NOTHING, null=True)

    cost_excl_vat = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, null=True)
    object_id = models.PositiveIntegerField(null=True)
    item = GenericForeignKey('content_type', 'object_id')
    item_descr = models.CharField(max_length=400)
    item_descr_extra = models.CharField(max_length=400, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Manager(models.Manager):
        def build_for_item(self, item):
            return self.model(
                order=self.instance,
                cost_excl_vat=item.cost_excl_vat,
                item=item,
                item_descr=item.descr_for_order,
                item_descr_extra=item.descr_extra_for_order,
            )

    objects = Manager()

    def save(self):
        if self.item is not None:
            # I have no idea why this dance is needed, but it is
            item = self.item
            item.save()
            self.item = item
        super().save()

    @property
    def cost_incl_vat(self):
        return int(self.cost_excl_vat * 1.2)

    @property
    def cost_pence_incl_vat(self):
        return 100 * self.cost_incl_vat

    @property
    def owner_name(self):
        item = self.item

        if item is None:
            return 'Refunded'
        elif item.pk:
            if item.owner:
                return item.owner.name
            else:
                return item.invitation().email_addr
        else:
            if item.owner:
                return item.owner.name
            else:
                return item.email_addr
