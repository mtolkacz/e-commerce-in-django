# Generated by Django 2.2.5 on 2020-04-29 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0039_auto_20200429_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discountstatus',
            name='name',
            field=models.CharField(default='Inactive', max_length=15),
        ),
    ]