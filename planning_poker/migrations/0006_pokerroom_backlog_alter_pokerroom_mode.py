# Generated by Django 5.1.3 on 2024-12-14 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planning_poker', '0005_pokerroom_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='pokerroom',
            name='backlog',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='pokerroom',
            name='mode',
            field=models.CharField(choices=[('unanimity', 'Unanimité'), ('absolute_majority', 'Majorité absolue')], max_length=20),
        ),
    ]
