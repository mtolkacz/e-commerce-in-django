# Generated by Django 2.2.10 on 2020-05-29 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_auto_20200529_2224'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocode',
            name='minimum_value',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
