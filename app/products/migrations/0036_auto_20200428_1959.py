# Generated by Django 2.2.5 on 2020-04-28 19:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0035_auto_20200428_1042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='set_id',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
