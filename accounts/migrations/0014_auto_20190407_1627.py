# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-04-07 16:27
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_auto_20190224_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminlink',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2019, 4, 7, 16, 27, 32, 85379)),
        ),
        migrations.AlterField(
            model_name='mobileverification',
            name='created_time',
            field=models.DateTimeField(default=datetime.datetime(2019, 4, 7, 16, 27, 32, 84501)),
        ),
    ]
