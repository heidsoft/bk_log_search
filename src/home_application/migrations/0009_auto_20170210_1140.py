# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0008_auto_20170110_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchhistory',
            name='search_time',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='host',
            name='status',
            field=models.IntegerField(verbose_name='\u72b6\u6001', choices=[(0, '\u53d1\u5e03\u4e2d'), (1, '\u4e0b\u67b6\u4e2d'), (2, '\u91c7\u96c6\u4e2d'), (3, '\u5f02\u5e38'), (4, '\u6210\u529f'), (5, '\u5df2\u4e0b\u67b6')]),
        ),
    ]
