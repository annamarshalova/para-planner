# Generated by Django 3.1.3 on 2021-04-24 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MSP', '0036_auto_20210423_2301'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hometask',
            name='identifier',
        ),
        migrations.AlterField(
            model_name='exam',
            name='topic',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='exam',
            name='type',
            field=models.CharField(blank=True, default='контрольная', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='time',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='settings',
            name='end_date',
            field=models.DateField(default='2021-04-24'),
        ),
        migrations.AlterField(
            model_name='settings',
            name='start_date',
            field=models.DateField(default='24.04.2021'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='time',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]