# Generated by Django 2.0.3 on 2018-07-22 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cfp', '0006_proposal_replied_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='all_rooms_event',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='proposal',
            name='conference_event',
            field=models.BooleanField(default=False),
        ),
    ]
