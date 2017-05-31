# -*- coding: utf-8 -*-
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect

from common.log import logger
from utils import get_app_by_user


def is_in(app_id, bk_token):
    app_list = get_app_by_user(bk_token)
    return app_id in (_app['app_id'] for _app in app_list)


def check_perm():
    """
    装饰器： 用户是否拥有调用该方法的权限
    """
    def _limits(view_func):
        @wraps(view_func)
        def _awrapper_view(request):
            user = request.user
            if request.method == 'GET':
                data_source = request.GET
            else:
                data_source = request.POST
            try:
                bk_token = request.COOKIES['bk_token']
                app_id = data_source.get("app_id")
            except Exception, e:
                logger.info(u"permission cookies,%s" % e)
                return HttpResponseRedirect("/")
            if not app_id or not app_id.isdigit() or int(app_id) < 0:
                raise PermissionDenied
            if user.is_superuser or is_in(app_id, bk_token):
                return view_func(request)
            raise PermissionDenied

        return _awrapper_view

    return _limits
