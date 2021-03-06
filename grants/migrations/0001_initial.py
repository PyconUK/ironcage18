# Generated by Django 2.0.3 on 2018-04-14 13:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('about_you', models.TextField()),
                ('about_why', models.TextField()),
                ('requested_ticket_only', models.BooleanField(choices=[(True, "I'd like to request a free ticket, but don't need other financial assistance"), (False, "I'd like to request a free ticket and additional financial assistance")])),
                ('amount_requested', models.TextField(blank=True)),
                ('cost_breakdown', models.TextField(blank=True)),
                ('sat', models.BooleanField()),
                ('sun', models.BooleanField()),
                ('mon', models.BooleanField()),
                ('tue', models.BooleanField()),
                ('wed', models.BooleanField()),
                ('applicant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='grant_application', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
