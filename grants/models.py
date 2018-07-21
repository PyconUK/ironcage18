from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse

from tickets.constants import DAYS

from ironcage.utils import Scrambler


class Application(models.Model):

    REQUESTED_TICKET_ONLY_CHOICES = [
        (True, "I'd like to request a free ticket, but don't need other financial assistance"),
        (False, "I'd like to request a free ticket and additional financial assistance"),
    ]

    applicant = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='grant_application', on_delete=models.CASCADE)

    about_you = models.TextField(blank=False)
    about_why = models.TextField(blank=False)

    requested_ticket_only = models.BooleanField(blank=False, choices=REQUESTED_TICKET_ONLY_CHOICES)

    amount_requested = models.TextField(blank=True)
    cost_breakdown = models.TextField(blank=True)
    ticket_awarded = models.BooleanField(default=False)
    amount_awarded = models.DecimalField(null=True, blank=True, max_digits=6, decimal_places=2)
    full_amount_awarded = models.BooleanField(default=False)
    application_declined = models.BooleanField(default=False)
    replied_to = models.DateTimeField(null=True)

    sat = models.BooleanField()
    sun = models.BooleanField()
    mon = models.BooleanField()
    tue = models.BooleanField()
    wed = models.BooleanField()

    id_scrambler = Scrambler(4000)

    class Manager(models.Manager):
        def get_by_application_id_or_404(self, application_id):
            id = self.model.id_scrambler.backward(application_id)
            return get_object_or_404(self.model, pk=id)

    objects = Manager()

    @property
    def application_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('grants:application', args=[self.application_id])

    def days(self):
        return [DAYS[day] for day in DAYS if getattr(self, day)]
