# Generated by Django 2.1.3 on 2019-04-05 09:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyDomain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('modified_time', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='companycategory',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='companycategory',
            name='category_value',
            field=models.CharField(max_length=250),
        ),
        migrations.AlterModelTable(
            name='companycategory',
            table=None,
        ),
        migrations.AddField(
            model_name='company',
            name='domain',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='company_management.CompanyDomain'),
        ),
    ]
