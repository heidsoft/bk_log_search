# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0010_searchhistory_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='publish_status',
            field=models.IntegerField(verbose_name='\u53d1\u5e03\u72b6\u6001', choices=[(0, '\u53d1\u5e03\u6210\u529f'), (1, '\u53d1\u5e03\u5931\u8d25'), (2, '\u53d1\u5e03\u4e2d'), (3, '\u4e0b\u67b6\u6210\u529f'), (4, '\u4e0b\u67b6\u5931\u8d25'), (5, '\u4e0b\u67b6\u4e2d')]),
        ),
    ]
