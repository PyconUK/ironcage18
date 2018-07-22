from django.conf import settings
from django.db import models

from cfp.models import Proposal
from tickets.constants import DAYS


class Room(models.Model):
    name = models.CharField(max_length=100)

    capacity = models.PositiveIntegerField()

    order = models.PositiveIntegerField()

    has_sttr = models.BooleanField()
    has_projector = models.BooleanField()
    has_screen = models.BooleanField()
    has_vga = models.BooleanField()
    has_hdmi = models.BooleanField()
    has_lectern = models.BooleanField()
    has_mic = models.BooleanField()
    has_stage = models.BooleanField()
    has_fixed_seating = models.BooleanField()

    accessible_auditorium = models.BooleanField()
    accessible_stage = models.BooleanField()
    accessibility_notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Stream(models.Model):

    STREAM_TYPE_CHOICES = (
        ('day', 'Daytime'),
        ('eve', 'Evening')
    )

    name = models.CharField(max_length=100)
    day = models.DateField()
    room = models.ForeignKey(Room, related_name='streams', on_delete=models.CASCADE)

    visible = models.BooleanField(default=False)

    stream_type = models.CharField(max_length=3, choices=STREAM_TYPE_CHOICES)

    def __str__(self):
        return self.name


class Session(models.Model):
    activity = models.ForeignKey(Proposal, related_name='session', on_delete=models.CASCADE)

    stream = models.ForeignKey(Stream, related_name='sessions', on_delete=models.CASCADE, blank=True, null=True)

    chair = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chaired_sessions',
                              on_delete=models.CASCADE, blank=True, null=True)
    additional_people = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    time = models.TimeField(blank=True, null=True)
    length = models.DurationField(blank=True, null=True)

    def __str__(self):
        return f'{self.activity.title} ({self.time})'

