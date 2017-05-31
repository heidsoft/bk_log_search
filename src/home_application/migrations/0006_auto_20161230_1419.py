# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0005_auto_20161228_1947'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='host',
            name='app_name',
        ),
        migrations.RemoveField(
            model_name='host',
            name='task_id',
        ),
    ]
