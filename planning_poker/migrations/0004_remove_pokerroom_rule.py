# Generated by Django 5.1.3 on 2024-12-14 19:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('planning_poker', '0003_pokerroom_rule'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pokerroom',
            name='rule',
        ),
    ]
