# Generated by Django 2.2.10 on 2020-06-02 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_auto_20200602_0024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='picture',
            field=models.ImageField(blank=True, default='avatar.png', null=True, upload_to='users/'),
        ),
    ]
