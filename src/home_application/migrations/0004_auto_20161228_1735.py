# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0003_auto_20161221_1221'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='config',
            name='app_name',
        ),
        migrations.RemoveField(
            model_name='config',
            name='task_id',
        ),
    ]
