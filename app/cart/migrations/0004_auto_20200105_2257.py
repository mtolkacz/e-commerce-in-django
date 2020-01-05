# Generated by Django 2.2.5 on 2020-01-05 22:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('cart', '0003_auto_20200105_2220'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile'),
        ),
        migrations.RemoveField(
            model_name='order',
            name='items',
        ),
        migrations.AddField(
            model_name='order',
            name='items',
            field=models.ManyToManyField(to='cart.OrderItem'),
        ),
        migrations.AlterField(
            model_name='order',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile'),
        ),
    ]
