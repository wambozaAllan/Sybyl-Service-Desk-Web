# Generated by Django 2.1.3 on 2019-05-16 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_auto_20190516_1809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directchat',
            name='chat_room_id',
            field=models.CharField(default=1, max_length=255),
        ),
    ]