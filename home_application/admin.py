# -*- coding: utf-8 -*-
from django.contrib import admin

from models import Config, DataId, Host, SearchHistory, Task

admin.site.register(Config)
admin.site.register(Task)
admin.site.register(Host)
admin.site.register(SearchHistory)
admin.site.register(DataId)
