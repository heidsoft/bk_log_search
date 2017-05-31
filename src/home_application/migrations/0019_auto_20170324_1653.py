# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0018_auto_20170322_1133'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchhistory',
            name='count_data',
            field=models.IntegerField(default=0, verbose_name='\u8fd4\u56de\u6761\u6570'),
        ),
        migrations.AddField(
            model_name='searchhistory',
            name='time_consume',
            field=models.TextField(null=True, verbose_name='\u67e5\u8be2\u8017\u65f6'),
        ),
    ]
