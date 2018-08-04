from django.conf import settings
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models

from ironcage.utils import Scrambler


class ExtraItem(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, null=True)
    object_id = models.PositiveIntegerField(null=True)
    item = GenericForeignKey('content_type', 'object_id')

    order_rows = GenericRelation('orders.OrderRow')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(6000)

    class Manager(models.Manager):

        def build(self, content_type, owner, details):
            assert details

            item_class = content_type.model_class()

            item = item_class(**details)

            item.save()

            extra_item = self.model(
                owner=owner,
                item=item,
            )

            return extra_item

    objects = Manager()

    @property
    def item_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    @property
    def descr_for_order(self):
        return "Young Coders' day ticket"

    @property
    def descr_extra_for_order(self):
        return ''

    @property
    def is_saved(self):
        return self.pk is not None

    @property
    def order_row(self):
        # We expect there to only ever be a single OrderRow, so this should never fail
        return self.order_rows.get()

    @property
    def order(self):
        if self.is_saved:
            return self.order_row.order
        else:
            return None

    @property
    def cost_excl_vat(self):
        if self.is_saved:
            return self.order_row.cost_excl_vat
        else:
            return self.item.cost_excl_vat

    @property
    def cost_incl_vat(self):
        return int(self.cost_excl_vat * 1.2)


class ChildrenTicket(models.Model):

    adult_name = models.CharField(max_length=255)
    adult_email_addr = models.CharField(max_length=255)
    adult_phone_number = models.CharField(max_length=255)
    accessibility_reqs = models.TextField(null=True, blank=True)
    dietary_reqs = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField(null=True, blank=True)

    cost_excl_vat = 5

    def __str__(self):
        return f'{self.name} ({self.age}) with {self.adult_name}'
