# Generated by Django 5.1.2 on 2025-01-24 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_order_name_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='order',
            name='number',
            field=models.IntegerField(max_length=15),
        ),
    ]
