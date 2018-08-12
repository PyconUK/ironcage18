from datetime import datetime

from django.conf import settings
from django.db import models

from cfp.models import Proposal


# This now uses the same naming convention as the PyCon UK Scheduler.
# Events come from proposals
# Slot is a room/time
# Session is a continuous set of slots (eg 'mid-morning')
#
# We are using our own room list to store extra metadata about rooms
# SlotEvent is the join table


class Room(models.Model):
    name = models.CharField(max_length=100)

    capacity = models.PositiveIntegerField()

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


class Slot(models.Model):

    EVENT_TYPE_CHOICES = (
        ('pre-allocated', 'Pre-allocated'),
        ('talk', 'Talk'),
        ('workshop', 'Workshop'),
        ('kidsworkshop', 'Kids Workshop'),
        ('teachersworkshop', 'Teachers Workshop'),
        ('teacherstalk', 'Teachers Talk')
    )

    room = models.ForeignKey(Room, related_name='streams', on_delete=models.CASCADE)
    date = models.DateField()
    session_name = models.CharField(max_length=30, blank=True, null=True)
    time = models.TimeField()
    duration = models.DurationField()
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)

    visible = models.BooleanField()
    scheduler_linked = models.BooleanField()

    def __str__(self):
        return f'{self.room} {self.date} {self.time} {self.event_type}'


class SlotEvent(models.Model):
    activity = models.ForeignKey(Proposal, related_name='session', on_delete=models.CASCADE)

    slot = models.ForeignKey(Slot, related_name='slots', on_delete=models.CASCADE, blank=True, null=True)

    chair = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chaired_slots',
                              on_delete=models.CASCADE, blank=True, null=True)
    additional_people = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    ical_id = models.CharField(max_length=8, null=False, blank=False)

    def __str__(self):
        return f'{self.activity.title} ({self.slot.time})'

    @property
    def end_time(self):
        return (datetime.combine(self.slot.date, self.slot.time) + self.slot.duration).time()


class Cache(models.Model):
    key = models.CharField(max_length=24, unique=True)
    value = models.TextField(null=True)
