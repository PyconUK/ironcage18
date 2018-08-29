from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404

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

        def get_by_item_id_or_404(self, item_id):
            id = self.model.id_scrambler.backward(item_id)
            return get_object_or_404(self.model, pk=id)

        def build(self, content_type, owner, details):
            assert details

            item_class = content_type.model_class()

            item = item_class(**details)

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
        if self.content_type.model_class() is ChildrenTicket:
            return "Young Coders' day ticket"
        elif self.content_type.model_class() is DinnerTicket:
            return f'{self.item} dinner ticket'
        else:
            assert False

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


CLINK_STARTERS = (
    ('ENB', 'Egg and bacon'),
    ('ESB', 'Egg, sausage and bacon'),
)

CLINK_MAINS = (
    ('ENS', 'Egg and Spam'),
    ('EBS', 'Egg, bacon and Spam'),
)

CLINK_DESSERTS = (
    ('EBSS', 'Egg, bacon, sausage and Spam'),
    ('SBSS', 'Spam, bacon, sausage and Spam'),
)

CITY_HALL_STARTERS = (
    ('SESS', 'Spam, egg, Spam, Spam, bacon and Spam'),
    ('SSSE', 'Spam, Spam, Spam, egg and Spam'),
)

CITY_HALL_MAINS = (
    ('SSSS', 'Spam, Spam, Spam, Spam, Spam, Spam, baked beans, Spam, Spam, Spam and Spam'),
    ('LTAC', 'Lobster Thermidor aux crevettes with a Mornay sauce, garnished with truffle pâté, brandy and a fried egg on top, and Spam.'),
)

CITY_HALL_DESSERTS = (
    ('ENB', 'Egg and bacon'),
    ('ESB', 'Egg, sausage and bacon'),
)

DINNER_LOCATIONS = {
    'CH': {
        'name': 'Conference Dinner at City Hall',
        'location': 'Lower Hall, Cardiff City Hall, Cathays Park, Cardiff',
        'capacity': 200,
        'price': 30,
    },
    'CL': {
        'name': 'The Clink',
        'location': 'HMP Cardiff, Knox Road, Cardiff',
        'capacity': 45,
        'price': 30,
    }
}

DINNERS = {
    'CD': {
        'location': 'CH',
        'date': '2018-09-15',
    },
    'CLSA': {
        'location': 'CL',
        'date': '2018-09-15',
    },
    'CLSU': {
        'location': 'CL',
        'date': '2018-09-16',
    },
    'CLMO': {
        'location': 'CL',
        'date': '2018-09-17',
    },
    'CLTU': {
        'location': 'CL',
        'date': '2018-09-18',
    },
    'CLWE': {
        'location': 'CL',
        'date': '2018-09-19',
    },
}

CLINK_DINNERS = (
    ('CLSA', 'The Clink on Saturday 15th September'),
    ('CLSU', 'The Clink on Sunday 16th September'),
    ('CLMO', 'The Clink on Monday 17th September'),
    ('CLTU', 'The Clink on Tuesday 18th September'),
    ('CLWE', 'The Clink on Wednesday 19th September'),
)

CITY_HALL_DINNERS = (
    ('CD', 'Conference Dinner at City Hall on Saturday 15th September'),
)


class DinnerTicket(models.Model):

    dinner = models.CharField(max_length=4, blank=False, choices=CLINK_DINNERS + CITY_HALL_DINNERS)
    starter = models.CharField(max_length=4, blank=False, choices=CLINK_STARTERS + CITY_HALL_STARTERS)
    main = models.CharField(max_length=4, blank=False, choices=CLINK_MAINS + CITY_HALL_MAINS)
    dessert = models.CharField(max_length=4, blank=False, choices=CLINK_DESSERTS + CITY_HALL_DESSERTS)

    def __str__(self):
        return f'{self.get_dinner_display()}'

    @property
    def cost_excl_vat(self):
        return DINNER_LOCATIONS[DINNERS[self.dinner]['location']]['price']

    @property
    def is_editable(self):
        beginning_of_dinner_day = datetime.strptime(DINNERS[self.dinner]['date'], '%Y-%m-%d')
        return datetime.now() < beginning_of_dinner_day
