# Generated by Django 2.2.19 on 2021-03-01 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MSP', '0003_auto_20210301_1926'),
    ]

    operations = [
        migrations.AddField(
            model_name='hometask',
            name='identifier',
            field=models.IntegerField(default=0),
        ),
    ]