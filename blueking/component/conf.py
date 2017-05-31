# -*- coding: utf-8 -*-
"""Django project settings
"""


try:
    from django.conf import settings

    APP_CODE = settings.APP_ID
    SECRET_KEY = settings.APP_TOKEN
except:
    APP_CODE = ''
    SECRET_KEY = ''

COMPONENT_SYSTEM_HOST = 'http://tc.open-esb.oa.com'

CLIENT_ENABLE_SIGNATURE = False
