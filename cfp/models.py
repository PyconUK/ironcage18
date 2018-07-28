from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ironcage.utils import Scrambler
from cfp.validators import validate_max_300_words


class Proposal(models.Model):
    SESSION_TYPE_CHOICES = (
        ('talk', 'A talk (25 minutes)'),
        ('workshop', 'A workshop (3 hours)'),
        ('poster', 'A poster'),
        ('kidsworkshop', 'Education Summit workshop for young coders (Saturday, 50 mins)'),
        ('teachersworkshop', 'Education Summit workshop for educators (Sunday, 50 mins)'),
        ('teacherstalk', 'Education Summit talk for educators (Sunday, 25 mins)'),
        ('other', 'Something else'),
    )

    STATE_TYPE_CHOICES = (
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
        ('accept', 'Accepted'),
        ('reject', 'Plan to Reject'),
        ('withdrawn', 'Withdrawn')
    )

    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='proposals', on_delete=models.CASCADE)
    session_type = models.CharField(max_length=40, choices=SESSION_TYPE_CHOICES)
    title = models.CharField(max_length=60)
    subtitle = models.CharField(max_length=120, blank=True)
    copresenter_names = models.TextField(blank=True)
    description = models.TextField(validators=[validate_max_300_words])
    description_private = models.TextField(validators=[validate_max_300_words], blank=True)
    outline = models.TextField(blank=True)
    equipment = models.TextField(blank=True)
    aimed_at_new_programmers = models.BooleanField()
    aimed_at_teachers = models.BooleanField()
    aimed_at_data_scientists = models.BooleanField()
    would_like_mentor = models.BooleanField()
    would_like_longer_slot = models.BooleanField()
    state = models.CharField(max_length=40, blank=True, choices=STATE_TYPE_CHOICES)
    track = models.CharField(max_length=40, blank=True)
    special_reply_required = models.BooleanField(default=False)
    scheduled_room = models.CharField(max_length=40, blank=True)
    scheduled_time = models.DateTimeField(null=True)
    coc_conformity = models.BooleanField()
    ticket = models.BooleanField()
    confirmed = models.DateTimeField(null=True)
    replied_to = models.DateTimeField(null=True)

    break_event = models.BooleanField(default=False)
    conference_event = models.BooleanField(default=False)

    length_override = models.DurationField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    id_scrambler = Scrambler(3000)

    class Meta:
        permissions = [
            ('review_proposal', 'Can review proposals'),
            ('review_education_proposal', 'Can review education proposals'),
        ]

    class Manager(models.Manager):
        def get_by_proposal_id_or_404(self, proposal_id):
            id = self.model.id_scrambler.backward(proposal_id)
            return get_object_or_404(self.model, pk=id)

        def accepted_talks(self):
            return self.filter(Q(session_type='talk') & Q(state='accepted'))

        def reviewed_by_user(self, user):
            return self.accepted_talks().filter(vote__user=user).order_by('id')

        def unreviewed_by_user(self, user):
            return self.accepted_talks().exclude(vote__user=user).order_by('id')

        def of_interest_to_user(self, user):
            return self.accepted_talks().filter(vote__user=user, vote__is_interested=True).order_by('id')

        def not_of_interest_to_user(self, user):
            return self.accepted_talks().filter(vote__user=user, vote__is_interested=False).order_by('id')

        def get_random_unreviewed_by_user(self, user):
            return self.unreviewed_by_user(user).order_by('?').first()

    objects = Manager()

    def __str__(self):
        return f'{self.title} ({self.proposal_id})'

    @property
    def proposal_id(self):
        if self.id is None:
            return None
        return self.id_scrambler.forward(self.id)

    def get_absolute_url(self):
        return reverse('cfp:proposal', args=[self.proposal_id])

    def full_title(self):
        if self.subtitle:
            return f'{self.title}: {self.subtitle}'
        else:
            return self.title

    @property
    def length(self):
        if self.length_override:
            return self.length_override
        elif self.session_type in ['talk', 'teacherstalk']:
            return timedelta(minutes=30)
        elif self.session_type == 'workshop':
            return timedelta(minutes=180)
        elif self.session_type in ['kidsworkshop', 'teachersworkshop']:
            return timedelta(minutes=60)
        else:
            return timedelta(minutes=0)
