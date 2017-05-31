# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0007_auto_20170106_1204'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='status',
            field=models.IntegerField(verbose_name='\u72b6\u6001', choices=[(0, '\u5df2\u4e0b\u67b6'), (1, '\u4e0b\u67b6\u4e2d')]),
        ),
    ]
