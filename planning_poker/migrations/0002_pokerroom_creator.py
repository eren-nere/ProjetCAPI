# Generated by Django 5.1.3 on 2024-12-02 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planning_poker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pokerroom',
            name='creator',
            field=models.CharField(default='Invité', max_length=50),
            preserve_default=False,
        ),
    ]
