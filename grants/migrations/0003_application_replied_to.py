# Generated by Django 2.0.3 on 2018-07-21 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grants', '0002_add_award_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='replied_to',
            field=models.DateTimeField(null=True),
        ),
    ]