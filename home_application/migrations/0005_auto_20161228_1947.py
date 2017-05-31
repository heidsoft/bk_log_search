# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0004_auto_20161228_1735'),
    ]

    operations = [
        migrations.RenameField(
            model_name='config',
            old_name='moudles',
            new_name='modules',
        ),
    ]
