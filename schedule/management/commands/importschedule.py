import re
import csv
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import get_template
from django.urls import reverse

from cfp.models import Proposal
from ironcage.emails import send_mail

from schedule.models import Stream, Room, Session


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        with open('/Users/kirk/Downloads/schedule.csv', 'r') as f:
            reader = csv.reader(f)
            for i, (event_index, event, slot_index, slot) in enumerate(reader):
                if i == 0:
                    continue
                # print(event_index, event, slot_index, slot)
                date, time, *room = slot.split(' ')
                room = ' '.join(room)

                try:
                    activity = Proposal.objects.get(title=event)
                except:
                    print(event)
                    continue

                room = Room.objects.get(name=room)

                try:
                    stream = Stream.objects.get(room=room, day=date, stream_type='day')
                except:
                    print(room, date)

                session = Session.objects.get_or_create(
                    activity=activity,
                    stream=stream,
                    time=time,
                    length=timedelta(minutes=30)
                )

