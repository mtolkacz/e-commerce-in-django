# Generated by Django 2.2.5 on 2019-09-28 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(default='No category', max_length=100, unique=True),
        ),
    ]