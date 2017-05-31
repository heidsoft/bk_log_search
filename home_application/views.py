# -*- coding: utf-8 -*-
import json

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import StreamingHttpResponse

from common.log import logger
from common.mymako import render_json, render_mako_context
from constants import ERROR_STATUS, ConfigStatus, HostStatus
from form import ConfigForm, QueryForm, SearchLogForm, CheckPublishIpsForm, HistogramLogForm
from models import Config, Host, Task
from utils import (check_app_validate, check_success_config, get_all_app_list,
                   get_app_by_user, get_log, get_module_by_ip, get_data_by_api,
                   get_modules_by_app, history_keys, issue_config, create_config_record,
                   query_host_result, start_publish_config, save_search_history,
                   get_collecting_ips, get_ip_by_app, get_ip_by_module, es_chart, form_excel)
from validators import check_perm


def index(request):
    """
    @summary:日志检索页面
    """
    user = request.user
    app_id = ''

    is_validate, app_choice = check_app_validate(
        request.COOKIES, app_id, user.is_superuser)

    if is_validate:
        return render_mako_context(request, "/home_application/index.html",
                                   {'app_id': app_choice})
    else:
        if not app_id:
            return render_mako_context(request, "/app_403.html")
        return render_mako_context(request, "/403.html")


@check_perm()
def check_app_config(request):
    """
    @summary:检查app是否有可用配置
    """
    app_id = request.POST.get("app_id", '')
    if not app_id:
        return render_json({"result": True})
    return render_json({"result": check_success_config(app_id)})


def get_app_list(request):
    """
    @summary:获取cc权限列表
    """
    if request.method != 'POST':
        return render_json({"result": False, "data": []})

    if request.user.is_superuser:
        app_list = get_all_app_list(request.COOKIES['bk_token'])
    else:
        app_list = get_app_by_user(request.COOKIES['bk_token'])
    for x in app_list:
        if x.get("app_name") == u'\u8d44\u6e90\u6c60':
            app_list.remove(x)
            break
    return render_json({"result": True, "data": app_list})


@check_perm()
def search_log(request):
    """
    @summary:日志查询接口
    """
    form = SearchLogForm(request.POST)
    if not form.is_valid():
        return render_json({
            "result": False, "data": {}, "message": u"参数错误"})

    key = form.cleaned_data["key"]
    start = form.cleaned_data["start"]
    app_id = form.cleaned_data["app_id"]

    is_success, error_code, data = get_log(
        form.cleaned_data["size"],
        start, key, request.COOKIES['bk_token'],
        app_id)

    if key and start == 0:
        save_search_history(request.user, app_id, key, data.get("took"), data.get("total") if data else 0)

    if is_success:
        return render_json({"result": True, "data": data, "message": ""})
    else:
        result = False
        if error_code == "20001":
            config_add_check = Config.objects.filter(app_id=app_id, publish_status=0, publish_type=0)
            config_off_check = Config.objects.filter(app_id=app_id, publish_status=0, publish_type=1)
            if config_off_check.count() < config_add_check.count():
                message = u"查询接口出错，请联系管理员查看"
                error_code = "20002"
            else:
                message = u"请创建采集项！"
        else:
            message = u"请修改查询关键词重试!"
            result = True
        return render_json(
            {"result": result,
             "data": {"total": 0, "took": 0, "log_list": []},
             "message": u"查询失败，%s" % message,
             "code": error_code})


@check_perm()
def get_history_keys(request):
    """
    @summary:获取历史搜索
    """
    if request.method != "POST":
        return render_json(
            {"result": False, "data": {}, "message": u"查询方法错误"})

    keys = history_keys(request.user, request.POST.get('app_id', ''))

    return render_json(
        {"result": True, "data": keys, "message": u""})


@check_perm()
def get_all_history_keys(request):
    """
    @summary:获取历史搜索
    """
    if request.method != "POST":
        return render_json(
            {"result": False, "data": {}, "message": u"查询方法错误"})

    keys = history_keys(request.user, request.POST.get('app_id', ''), "all")

    return render_json(
        {"result": True, "data": keys, "message": u""})


@check_perm()
def get_chart_data(request):
    """
    :return:
    """
    form = HistogramLogForm(request.POST)
    if not form.is_valid():
        return render_json({
            "result": False, "data": {}, "message": u"参数错误"})
    keyword = form.cleaned_data["keyword"]
    app_id = form.cleaned_data["app_id"]
    date_inteval = form.cleaned_data["date_inteval"]
    chart_data, date_inteval, timetaken = es_chart(app_id, request.COOKIES['bk_token'], keyword, date_inteval)
    return render_json({"result": True,
                        "data": {"date_inteval": date_inteval,
                                 "chart_data": chart_data},
                        "timetaken": timetaken,
                        "message": u"请求成功"})


@check_perm()
def query_config(request):
    """
    @summary:配置记录
    """
    form = QueryForm(request.GET)
    if not form.is_valid():
        return render_json({"data": [], "total_count": 0, "status": False})

    sort = form.cleaned_data['sort']
    if not sort:
        sort = "-id"

    config_list = Config.objects.filter(
        app_id=form.cleaned_data["app_id"]).order_by(sort, "-id")
    total = config_list.count()

    start = form.cleaned_data['offset']
    end = start + form.cleaned_data['length']

    config_json = Config.to_json(config_list[start: end])

    return render_json({
        "status": True,
        'data': config_json,
        'total_count': total,
    })


@check_perm()
def get_modules(request):
    """
    @summary:获取业务下所有模块列表
    """
    if request.method != "POST":
        return render_json({"status": False, "data": [],
                            "message": u"请求方法错误"})
    app_id = request.POST.get("app_id", '')
    bk_token = request.COOKIES['bk_token']

    modules = list(set(get_modules_by_app(app_id, bk_token)))

    hosts = get_ip_by_app(app_id, bk_token)

    modules_data = []
    for module in modules:
        ip_data = get_ip_by_module(hosts, module)
        modules_data.append({"module": module, "ip_total": len(ip_data)})

    return render_json({"status": True, "data": modules_data,
                        "message": ""})


@check_perm()
def publish_config(request):
    """
    @summary:下发配置
    """
    # 考虑所有配置会有元素为空 比如255.1.1.1，，，
    form = ConfigForm(request.POST)
    if not form.is_valid():
        return render_json({
            "status": False, "data": [], "message": u"数据不合法"})
    json_data = start_publish_config(form.cleaned_data,
                                     request.COOKIES.get('bk_token', ''),
                                     request.user)

    return render_json(json_data)


@check_perm()
def get_config_status(request):
    """
    @summary:轮询下发配置状态
    """
    try:
        config_id = request.POST['id']
        status = Task.objects.filter(source_id=config_id)
        p_config = Config.objects.get(id=config_id)
        status_dic = json.loads(status[0].status)
        status_dic['1'].update({'title': u"生成配置信息"})
        status_dic['2'].update({'title': u"下发配置信息"})
        status_dic.update(
            {"finish_status": p_config.publish_status})
        return render_json({'result': True, 'status': status_dic})
    except:
        return render_json({'result': False, 'status': ERROR_STATUS})


@check_perm()
def query_module_config(request):

    '''
    |参数名|必选|类型|说明|样例|
    |:--------    |:---|:------|:-----  |-------   |
    |length |是  |int |分页长度   |‘10’|
    |app_id |是  |int |业务ID   |‘10’|
    |offset |是  |int |分页起始位置 |‘10’|
    |value |否  |string |搜索关键词 |‘data’|
    '''
    form = QueryForm(request.GET)
    if not form.is_valid():
        return render_json({"data": [], "total_count": 0, "result": False})
    q = Q()
    value = form.cleaned_data['value']
    if value:
        q = (Q(ip__contains=value) | Q(paths__contains=value) | Q(module__contains=value))

    sort = form.cleaned_data['sort']
    if not sort:
        sort = "-id"

    start = form.cleaned_data['offset']
    end = start + form.cleaned_data['length']

    host_list = Host.objects.select_related().filter(
        q, app_id=form.cleaned_data["app_id"]).order_by(sort, '-id')

    for host_check in host_list:
        if host_check.status in [int(HostStatus.COLLECTING),
                                 int(HostStatus.SUCCESS),
                                 int(HostStatus.STATUS_EXCEPTION)
                                 ]:
            if host_check.is_get_status:
                continue
            host_check.is_get_status = True
            host_check.save()
            query_host_result(form.cleaned_data['app_id'], host_check,
                              request.COOKIES.get('bk_token', ''))
    bk_token = request.COOKIES['bk_token']
    hosts = get_ip_by_app(form.cleaned_data["app_id"], bk_token)

    module_ip_count_list = {}
    modules = list(set(get_modules_by_app(form.cleaned_data["app_id"], bk_token)))
    for module in modules:
        ip_data = get_ip_by_module(hosts, module)
        module_ip_count_list[module] = len(ip_data)
    module_list = Host.to_module_json(host_list, module_ip_count_list)
    total = len(module_list)
    data = {
        "result": True,
        "total_count": total,
        "data": module_list[start:end]
    }
    return render_json(data)

@check_perm()
def query_host(request):
    """
    @summary:主机管理分页
    """
    form = QueryForm(request.GET)
    if not form.is_valid():
        return render_json({"data": [], "total_count": 0, "status": False})
    q = Q()
    value = form.cleaned_data['value']
    if value:
        q = (Q(ip__contains=value) | Q(paths__contains=value))

    sort = form.cleaned_data['sort']
    if not sort:
        sort = "-id"

    start = form.cleaned_data['offset']
    end = start + form.cleaned_data['length']

    host_list_check = (Host.objects.filter(q, app_id=form.cleaned_data["app_id"]
                                           ).order_by(sort, '-id')[start: end])
    host_list = Host.objects.filter(
        q, app_id=form.cleaned_data["app_id"]).order_by(sort, '-id')

    for host_check in host_list_check:
        if host_check.status in [int(HostStatus.COLLECTING),
                                 int(HostStatus.SUCCESS),
                                 int(HostStatus.STATUS_EXCEPTION)
                                 ]:
            if host_check.is_get_status:
                continue
            host_check.is_get_status = True
            host_check.save()
            query_host_result(form.cleaned_data['app_id'], host_check,
                              request.COOKIES.get('bk_token', ''))

    total = host_list.count()

    host_json = Host.to_json(host_list[start: end])

    return render_json({
        "status": True,
        'data': host_json,
        'total_count': total,
    })


@check_perm()
def host_module_off(request):
    """
        @summary:下架配置
    """
    module = request.POST.get("module", "")
    app_id = request.POST.get("app_id", "")
    ip_module = []
    ip_list = []
    host_ip_list = Host.objects.filter(module=module, app_id=app_id)
    hosts = get_ip_by_app(app_id, request.COOKIES.get('bk_token', ''))
    for item in host_ip_list:
        host = Host.objects.get(ip=item.ip)
        if host.status in [int(HostStatus.COLLECTING)]:
            plat_id = ''
            for each in hosts:
                if each["InnerIP"] == host.ip and each["ModuleName"] == host.module:
                    plat_id = each["Source"]
            ip_module.append({"ip": item.ip, "module": item.module, "plat_id": plat_id})
            ip_list.append(item.ip)
        else:
            host.delete()
    config_request_para = {
        'path': [],
        'ex_files': [],
        'app_id': app_id,
        'ip_list': ip_list,
        'ip_module': ip_module,
        'user': request.user,
        'ips_source': 1,
        'modules': module,
        'bk_token': request.COOKIES.get('bk_token', '')
    }
    conf = create_config_record(config_request_para)
    issue_config.apply_async([config_request_para, conf.id])
    #issue_config(config_request_para, conf.id)
    return render_json({"status": True,
                        "data": [{"id": "", "status": u"采集项删除中"}],
                        "message": ""})


@check_perm()
def host_off(request):
    """
    @summary:主机下架
    """
    data = request.POST
    try:
        host = Host.objects.get(id=data.get('id', -1))
    except ObjectDoesNotExist:
        logger.warning(u"主机下架，ID不存在%s" % data.get('id', -1))
        return render_json({"status": False,
                            "data": [], "message": u"采集项删除操作失败"})
    if host.status in [int(HostStatus.REMOVING), int(HostStatus.WAITING)]:
        return render_json({"status": True,
                            "data": [{"id": '', "status": u"采集项删除中"}],
                            "message": u"采集项已经在删除中"})
    ip = host.ip
    result, host_module = get_module_by_ip(request.COOKIES['bk_token'],
                                           data['app_id'], ip)
    hosts = get_data_by_api('/api/c/compapi/cc/get_module_host_list/',
                            {'bk_token': request.COOKIES.get('bk_token', ''), "app_id": host.app_id, "module_id": host_module})
    logger.error(u'hosts: %s' % hosts)
    plat_id = ''
    for item in hosts:
        if item["InnerIP"] == ip:
            plat_id = item["Source"]
    if result:
        config_request_para = {
            'path': [],
            'ex_files': [],
            'app_id': data["app_id"],
            'ip_list': [ip],
            'ip_module': [{'ip': ip, 'module': host_module, 'plat_id': plat_id}],
            'user': request.user,
            'ips_source': 1,
            'modules': host_module,
            'bk_token': request.COOKIES.get('bk_token', '')
        }
        conf = create_config_record(config_request_para)
        logger.error(u'config_request_para: %s' % config_request_para)
        issue_config.apply_async([config_request_para, conf.id])
        #issue_config(config_request_para, conf.id)
        return render_json({"status": True,
                            "data": [{"id": "", "status": u"采集项删除中"}],
                            "message": ""})
    else:
        return render_json(
            {"status": False, "data": [], "message": u"采集项删除操作失败"})


@check_perm()
def query_config_status(requests):
    """
    @summary:轮询表格中发布中配置状态，返回是否有下发配置结束
    """
    app_id = requests.POST.get('app_id')
    config_id_list = requests.POST.get('config_id_list', '')
    if not config_id_list:
        return render_json({'status': False, 'data': {'result': False}})
    config_id_list = config_id_list.split(',')

    result = Config.objects.filter(~Q(
        publish_status=ConfigStatus.WORKING),
                                   app_id=app_id,
                                   id__in=config_id_list).exists()

    return render_json({'status': True, 'data': {'result': result}})


@check_perm()
def query_host_status(requests):
    """
    @summary:轮询表格中下架中配置状态，返回是否有下架结束
    @author:libywang
    """
    app_id = requests.POST.get('app_id')
    host_id_status = requests.POST.get('host_id_status', '')
    if not host_id_status:
        return render_json({'status': False, 'data': {'result': False}})
    try:
        host_id_status = json.loads(host_id_status)
    except Exception as e:
        logger.info(u"主机状态轮询接口，参数错误 %s %s" % (host_id_status, e))
        return render_json({'status': False, 'data': {'result': False}})
    host_id_list = host_id_status.keys()

    result = Host.objects.filter(app_id=app_id,
                                 id__in=host_id_list)

    if result.count() < len(host_id_list):
        return render_json({'status': True, 'data': {'result': True}})

    publishing_result = Host.objects.filter(app_id=app_id,
                                            status__in=[HostStatus.RELEASING, HostStatus.REMOVING]).exclude(id__in=host_id_list)
    if publishing_result:
        return render_json({'status': True, 'data': {'result': True}})

    is_change = False
    for host_status in result:
        if host_status.get_status_display() \
                != host_id_status[str(host_status.id)]:
            is_change = True
            break

    return render_json({'status': True, 'data': {'result': is_change}})


@check_perm()
def get_host_status(request):
    """
    @summary:轮询主机下架状态
    """
    try:
        task_id = request.POST['id']
        task = Task.objects.get(id=task_id)
        host_config = Config.objects.get(id=task.source_id)
        status = task.status

        status_dic = json.loads(status)
        status_dic['1'].update({'title': u"生成配置信息"})
        status_dic['2'].update({'title': u"下发配置信息"})
        status_dic.update(
            {"finish_status": host_config.publish_status})
        return render_json({'result': True, 'status': status_dic})
    except:
        return render_json({'result': False, 'status': ERROR_STATUS})


@check_perm()
def check_publish_ips(request):
    """
    下发前检查会有多少采集项配置被覆盖
    """
    form = CheckPublishIpsForm(request.POST)

    if not form.is_valid():
        return render_json({"result": False, "data": {"total": 0}})

    is_success, total, ip_list = get_collecting_ips(form.cleaned_data,
                                                    request.COOKIES['bk_token'])

    return render_json({"result": is_success,
                        "data": {"total": total, 'ip_list': ip_list}})


@check_perm()
def export_log(request):
    """
    @summary:日志下载接口
    """
    key = request.GET.get('key', '')
    start = request.GET.get('start', '')
    app_id = request.GET.get('app_id', '')
    size = request.GET.get('size', '')
    is_success, error_code, data = get_log(
        size,
        start, key, request.COOKIES['bk_token'],
        app_id)
    file_abs = "log_%s.txt" % app_id

    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    with open(file_abs, "wt") as f:
        for k in data.get("log_list"):
            log_k = [k.get("moduleName"), "  ", str(k.get("tagTime")), "  ", k.get("log").encode("utf-8"), "  ", k.get("serverIp"), "  ", k.get("localTime"), "\n"]
            f.writelines(log_k)
        f.writelines("Finish it")
        f.close()
    response = StreamingHttpResponse(file_iterator(file_abs), content_type='text/plain')
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_abs)
    return response


