# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0014_searchhistory_search_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='status',
            field=models.IntegerField(verbose_name='\u72b6\u6001', choices=[(0, '\u53d1\u5e03\u4e2d'), (1, '\u5220\u9664\u4e2d'), (2, '\u91c7\u96c6\u4e2d'), (3, '\u53d1\u5e03\u5f02\u5e38'), (4, '\u6210\u529f'), (5, '\u5220\u9664\u5f02\u5e38'), (6, '\u72b6\u6001\u5f02\u5e38')]),
        ),
    ]
