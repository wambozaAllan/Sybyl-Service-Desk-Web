# Generated by Django 2.1.3 on 2019-04-09 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_management', '0004_auto_20190409_1050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companydomain',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]