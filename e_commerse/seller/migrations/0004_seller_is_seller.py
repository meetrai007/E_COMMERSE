# Generated by Django 5.1.2 on 2024-12-26 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seller', '0003_seller_last_login'),
    ]

    operations = [
        migrations.AddField(
            model_name='seller',
            name='IS_seller',
            field=models.BooleanField(default=True),
        ),
    ]
