# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0012_dataid_is_create_es'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='publish_type',
            field=models.IntegerField(default=0, verbose_name='\u53d1\u5e03\u5185\u5bb9', choices=[(0, '\u65b0\u589e\u914d\u7f6e'), (1, '\u4e0b\u67b6\u4e3b\u673a')]),
        ),
        migrations.AlterField(
            model_name='config',
            name='publish_status',
            field=models.IntegerField(verbose_name='\u53d1\u5e03\u72b6\u6001', choices=[(0, '\u53d1\u5e03\u6210\u529f'), (1, '\u53d1\u5e03\u5931\u8d25'), (2, '\u53d1\u5e03\u4e2d')]),
        ),
    ]
