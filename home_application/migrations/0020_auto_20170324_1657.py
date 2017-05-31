# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0019_auto_20170324_1653'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchhistory',
            old_name='time_consume',
            new_name='took',
        ),
        migrations.RenameField(
            model_name='searchhistory',
            old_name='count_data',
            new_name='total',
        ),
    ]
