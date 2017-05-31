# -*- coding: utf-8 -*-
import copy
import datetime
import json
import re
import time
import unicodedata
import xlwt
from HTMLParser import HTMLParser

from django.core.exceptions import ObjectDoesNotExist
import requests
from celery import task
from djcelery.models import PeriodicTask, CrontabSchedule

from common.log import logger
from conf.default import APP_ID, APP_TOKEN, BK_PAAS_HOST
from constants import (BODY_DATA, DATA_SET, HEADERS, REQUEST_CREATE_DATA_ID,
                       REQUEST_GET_PRO_STATUS, REQUEST_RESULT_TABLE,
                       ConfigStatus, HostStatus, PublishType)
from models import Config, DataId, Host, SearchHistory, Task


def html_decode(key):
    """
    @summary:符号转义
    """
    h = HTMLParser()
    cleaned_text = unicodedata.normalize("NFKD", h.unescape(key).strip())
    return cleaned_text


def check_special_string(string):
    """
    @summary:是否含有特殊字符
    """
    s = (r"['!', '\"', '&', ')', '(', '+', '*', '-', '\\', ':', '\]',"
         r" '\[', '{', '~', '}', '|', '?', '^']")
    return re.search(s, string)


def get_data_by_api(url, request_data):
    """
    @summary:组装接口
    """
    url = BK_PAAS_HOST + url
    request_data.update({'app_code': APP_ID, 'app_secret': APP_TOKEN})
    try:
        result = requests.get(url, request_data, timeout=100)
        data = json.loads(result.text)['data']
        return data or []
    except Exception as e:
        logger.error(u'获取API%s信息失败%s %s ' % (url, request_data, e))
        return []


def get_app_by_user(bk_token):
    """
    @summary:查询用户有权限的业务
    """
    data = get_data_by_api('/api/c/compapi/cc/get_app_by_user/',
                           {'bk_token': bk_token})
    app_list = [{"app_name": app['ApplicationName'],
                 "app_id": app['ApplicationID']} for app in data]
    return app_list


def get_ip_by_app(app_id, bk_token):
    """
    @summary:查询模块下面所有主机
    """
    hosts = get_data_by_api('/api/c/compapi/cc/get_app_host_list/',
                            {'bk_token': bk_token, "app_id": app_id})

    return hosts


def get_modules_by_app(app_id, bk_token):
    # """
    # @summary:查询业务下面所有模块
    # """
    # modules = get_data_by_api('/api/c/compapi/cc/get_modules/',
    #                           {'bk_token': bk_token, "app_id": app_id})
    # return modules
    """
       @summary:查询业务下面所有模块
       """
    modules = get_data_by_api('/api/c/compapi/cc/get_modules/',
                              {'bk_token': bk_token, "app_id": app_id})
    try:
        modules = [item['ModuleName'] for item in modules]
    except:
        pass
    return modules


def get_module_by_ip(bk_token, app_id, ip):
    """
    @summary:根据主机IP获取主机所属模块
    """
    host_info = get_data_by_api('/api/c/compapi/cc/get_host_list_by_ip/',
                                {'bk_token': bk_token, 'app_id': app_id,
                                 'ip': ip})
    if host_info:
        return True, host_info[0]['ModuleName']
    else:
        return False, None


def get_all_app_list(bk_token):
    """
    @summary:超级管理员获取所有业务列表
    """
    data = get_data_by_api('/api/c/compapi/cc/get_app_list/',
                           {'bk_token': bk_token})
    app_list = [{"app_name": app['ApplicationName'],
                 "app_id": app['ApplicationID']} for app in data]
    return app_list


def check_app_validate(cookie, app_id, is_superuser):
    """
    @summary:判断用户是否有app权限
    """
    bk_token = cookie['bk_token']
    if is_superuser:
        app_list = get_all_app_list(bk_token)
    else:
        app_list = get_app_by_user(bk_token)

    if not app_list:
        return False, None

    if not app_id:
        if 'app_id' in cookie and cookie['app_id'] in (
                _app['app_id'] for _app in app_list):
            return True, cookie['app_id']
        else:
            return True, app_list[0]['app_id']

    validate = app_id in (_app['app_id'] for _app in app_list)
    return validate, app_id


def get_data_id_by_app_id(app_id, bk_token):
    """
    @summary:查询是否已经创建过data_id
    """
    data = get_data_by_api("api/c/compapi/data/databus/list_datasets/",
                           {"biz_id": app_id, "bk_token": bk_token})
    result = []
    for _data in data:
        if _data['data_set'] == DATA_SET and _data['op_platform'] == APP_ID:
            result.append(_data)
    return result


def check_success_config(app_id):
    """
    检查当前app是否有可用配置
    """
    return Config.objects.filter(
        app_id=app_id,
        publish_status=ConfigStatus.SUCCESS).exists()


def create_body_data(size, start, search_key):
    """
    日志查询构造请求参数
    """
    body_data = copy.deepcopy(BODY_DATA)
    body_data.update({
        "size": size,
        "from": start,
    })

    # todo 其他分词字符
    key_list = search_key.split(' ')
    query_list = []

    # 包含特殊字符则不加通配符，否则拿通配符包裹
    for query_key in key_list:
        if not query_key:
            continue
        pattern = "%s" if check_special_string(query_key) else "*%s*"
        # tmp_str = []
        # for i in range(0, len(query_key)):
        #     tmp_str.append(query_key[i])
        #     if query_key[i] in ['!', ':', '/', '\\', '[', ']', '?', '&', '-', '{', '}', '>', '<']:
        #         tmp_str[i] = '\\' + query_key[i]
        # re_string = ''.join(tmp_str)
        query_list.append(pattern % query_key)

    query_str = ' '.join(query_list)

    body_data['query']['query_string']['query'] = query_str

    if search_key == '':
        body_data.pop('query')

    return body_data


def save_search_history(user, app_id, key, took, total):
    """
    保存搜索历史
    """
    try:
        his_key, is_new = SearchHistory.objects.get_or_create(
            user=user,
            app_id=app_id,
            search_key=html_decode(key))
    except Exception, e:
        return
    his_key.search_time = datetime.datetime.now()
    his_key.search_date = datetime.date.today()
    his_key.took = took
    his_key.total = total
    his_key.count = 1 if is_new else his_key.count + 1
    his_key.save()


def get_log(size, start, search_key, bk_token, app_id):
    """
    @summary:查询日志
    """
    index = "%s_%s_%s*" % (app_id, DATA_SET, datetime.datetime.now().year)
    body_data = create_body_data(size, start, search_key)

    code = None
    result = {"text": ""}
    try:
        request_para = {
            'app_code': APP_ID,
            'app_secret': APP_TOKEN,
            'bk_token': bk_token,
            'prefer_storage': "es",
            'sql': json.dumps({'index': index, 'body': body_data}),
        }
        url = '%sapi/c/compapi/data/maple/get_data/' % BK_PAAS_HOST
        result = requests.post(url, json.dumps(request_para), headers=HEADERS, timeout=100)
        text = json.loads(result.text)
        code = text['code']
        search_result = text['data']['list']
    except Exception as e:
        logger.error(u"get_log, 查询出错：%s %s" % (e, result.text))
        return False, code, {}

    log_list = []

    for hit in search_result["hits"]["hits"]:
        log = hit["_source"]
        if "highlight" not in hit:
            log_list.append(log)
            continue
        for key in hit["highlight"]:
            log[key] = "".join(hit["highlight"][key])
        log_list.append(log)

    result = {"total": search_result["hits"]["total"],
              "took": round(float(search_result["took"]) / float(1000), 3),
              "log_list": log_list}

    return True, code, result


def history_keys(user, app_id, operate=None):
    """
    @summary:获取历史查询记录
    """

    key_data = []
    keys = SearchHistory.objects.filter(
        app_id=app_id,
    ).order_by("-search_time")
    new_keys=[]
    for index in keys:
        data = {"search_key": index.search_key, "total": index.total, "took": index.took,
                "search_time": str(index.search_time) if index.search_time else "", "count": index.count}
        if data.get("search_key") not in key_data:
            key_data.append(index.search_key)
            new_keys.append(data)
        else:
            continue
            index = key_data.index(data.get("search_key"))
            new_keys[index]["count"] += data.get("count")
            if new_keys[index].get("search_time") < data.get("search_time"):
                new_keys[index]["search_total"] = data.get("search_total")
                new_keys[index]["search_time"] = data.get("search_time")
            else:
                new_keys[index]["search_total"] = data.get("search_total")
    # new_keys.sort(key=lambda x: (x["search_time"], x["count"]), reverse=True)
    return new_keys


def get_ip_by_module(hosts, moudle):
    result = [host for host in hosts if host["ModuleName"] == moudle]
    return result


def start_publish_config(form, bk_token, user):
    """
    @summary:获取IP对应模块，开始下发配置
    """
    # 根据用户是按模块下发，还是手动输入IP下发，分别组装ip_module
    ip_module = []
    cmd_type = 1
    if form['ips_source'] == '0':
        module_list = form["modules"].split(",")
        ip_list = []
        hosts = get_ip_by_app(form["app_id"], bk_token)

        no_ip_module = []

        for module in module_list:
            ip_data = get_ip_by_module(hosts, module)
            module_ip_data = Host.objects.filter(module=module, app_id=form["app_id"])
            if not ip_data:
                no_ip_module.append(module)

            for item in ip_data:
                if item["InnerIP"] not in ip_list:
                    ip_module.append({'ip': item["InnerIP"], 'module': module, 'plat_id': item["Source"]})
                    ip_list.append(item["InnerIP"])
            for item in module_ip_data:
                if item.ip not in ip_list:
                    host = []
                    data_id = DataId.objects.get(app_id=item.app_id).data_id
                    if item.status in [int(HostStatus.COLLECTING)]:
                        hosts_off = get_ip_by_app(form["app_id"], bk_token)
                        plat_id = ''
                        for each in hosts_off:
                            if each["InnerIP"] == item.ip:
                                plat_id = each["Source"]
                        host.append({'ip': item.ip, "module": item.module, "plat_id": plat_id})
                        # deploy_collector(data_id, bk_token, hosts, files, app_id, ignore_file)
                    deploy_collector(data_id, bk_token, host, [], item.app_id, form["ex_files"].split(','))
                    item.delete()
        if no_ip_module:
            return {"status": False, "data": [],
                    "message": u"下发的模块（%s）不包含任何IP"
                               % ','.join(no_ip_module)}
    else:
        ip_list = form["ips"]
        no_module_ips = []
        if Host.objects.filter(ip__in=ip_list, status=HostStatus.DELETE_EXCEPTION).exists():
            cmd_type = 0
        for ip in ip_list:
            cc_result, module_name = get_module_by_ip(
                bk_token,
                form["app_id"], ip)
            hosts_off_ip = get_ip_by_app(form["app_id"], bk_token)
            if cc_result:
                plat_id = ''
                for each in hosts_off_ip:
                    if each["InnerIP"] == ip and each["ModuleName"] == module_name:
                        plat_id = each["Source"]
                ip_module.append({'ip': ip, 'module': module_name, 'plat_id': plat_id})
            else:
                no_module_ips.append(ip)
                host = Host.objects.get(ip=ip)
                plat_id = ''
                for each in hosts_off_ip:
                    if each["InnerIP"] == host.ip:
                        plat_id = each["Source"]
                hosts = [{'id': host.ip, "module": host.module, 'plat_id': plat_id}]
                data_id = DataId.objects.get(app_id=host.app_id).data_id
                if host.status in [int(HostStatus.COLLECTING)]:
                    deploy_collector(data_id, bk_token, hosts, [], host.app_id, form["ex_files"].split(','))
                host.delete()
        if no_module_ips:
            return {"status": False, "data": [],
                    "message": u"您输入的IP中包含非本业务IP（%s）"
                    % ','.join(no_module_ips)}

    # 开始下发配置
    config_request_para = {
        'path': form["paths"].split(',') if cmd_type else [],
        'ex_files': form["ex_files"].split(','),
        'app_id': form["app_id"],
        'ip_list': ip_list,
        'ip_module': ip_module,
        'user': user,
        'ips_source': form["ips_source"],
        'modules': form["modules"],
        'bk_token': bk_token
    }

    # 执行任务之前先创建等待记录
    conf = create_config_record(config_request_para)

    # issue_config(config_request_para,conf.id)
    issue_config.apply_async([config_request_para, conf.id])
    return {"status": True, "data": [{"id": '', "status": u"发布中"}],
            "message": ""}


def create_config_record(config_request_para):
    """
    下发配置前生成等待记录
    """
    file_name = config_request_para['path']
    ip_module = config_request_para['ip_module']
    host_status = HostStatus.WAITING
    config_status = ConfigStatus
    publish_type = (PublishType.PUBLUSH_CONFIG if file_name
                    else PublishType.HOST_OFF)

    conf = Config.objects.create(
        publish_time=datetime.datetime.now(),
        publish_user=config_request_para['user'],
        publish_status=config_status.WORKING,
        publish_type=publish_type,
        app_id=config_request_para['app_id'],
        ips_source=config_request_para['ips_source'],
        modules=config_request_para['modules'],
        ips=",".join(config_request_para['ip_list']),
        paths=",".join(file_name),
        ex_files=','.join(config_request_para['ex_files'])
    )

    for item in ip_module:
        Host.objects.update_or_create(defaults={
            "module": item['module'],
            "status": host_status,
            "app_id": conf.app_id,
            "config": conf,
            "paths": conf.paths,
            "is_get_status": False,
        }, ip=item['ip'])

    # 先根据文件路径是否为空判断任务来源,并创建Task记录
    source = 0 if file_name else 1

    Task.objects.create(source=source,
                        source_id=conf.id,
                        status=json.dumps({
                            "1": {"status": "working",
                                  "errcode": "",
                                  "error_message": ""
                                  }
                        }))
    return conf


def update_host_status(conf, host_status):
    Host.objects.filter(config = conf).update(status = host_status)


@task(ignore_result=True)
def issue_config(config_request_para, conf_id):
    """
    @summary:下发配置(主机下架)，分两步1.生成配置文件 2.下发配置文件
    """
    file_name = config_request_para['path']
    source = 0 if file_name else 1
    ip_module = config_request_para['ip_module']
    bk_token = config_request_para['bk_token']
    host_status = HostStatus.RELEASING if file_name else HostStatus.REMOVING
    host_exception = (HostStatus.PUBLISH_EXCEPTION
                      if file_name else HostStatus.DELETE_EXCEPTION)
    config_status = ConfigStatus

    try:
        conf = Config.objects.get(id=conf_id)
    except ObjectDoesNotExist:
        logger.info(u"下发配置信息不存在")
        return False

    # 下发配置之前先创建一个超时处理的任务
    task_params = {"conf_id": conf.id, "host_exception": host_exception}
    registed_task = "home_application.utils.clean_timeout_task"
    task_name = "clean_timeout_task_%s" % conf.id
    create_period_task(task_params, registed_task, task_name)

    #任务开始执行的时候更新host状态为执行中的状态
    update_host_status(conf, host_status)

    # 先检查本地是否存有该app对应的data_id，
    # 然后调接口查询该应用是否已经创建过data_id, 都没有则调接口创建data_id
    find_data_id_in_db = DataId.objects.filter(app_id=conf.app_id)
    find_existed_data_id = get_data_id_by_app_id(conf.app_id, bk_token)

    if not find_data_id_in_db.exists() and not find_existed_data_id:
        data_id = get_data_id_api(conf.app_id,
                                  conf.publish_user.username, bk_token)
        if not data_id['result']:
            Task.objects.filter(source_id=conf.id).update(
                status=json.dumps({
                    "1": {"status": "failed",
                          "errcode": data_id['code'],
                          "error_message": data_id['message']
                          }
                }))
            Config.objects.filter(id=conf.id).update(
                publish_status=config_status.FAILED)
            Host.objects.filter(config=conf).update(
                status=host_exception
            )
            return
        else:
            data_id_use = data_id['data']['data_id']
    else:
        if not find_data_id_in_db.exists() and find_existed_data_id:
            data_id_use = find_existed_data_id[0]['data_id']
            data_id = DataId.objects.create(app_id=conf.app_id,
                                            data_id=data_id_use)
        else:
            data_id_use = find_data_id_in_db[0].data_id
            data_id = find_data_id_in_db[0]

        if not data_id.is_create_es:
            is_create_es = create_es(config_request_para['app_id'],
                                     bk_token, data_id_use)
            if is_create_es:
                data_id.is_create_es = True
                data_id.save()
            else:
                data_id.is_create_es = False
                data_id.save()
                Task.objects.filter(source_id=conf.id).update(
                    status=json.dumps({
                        "1": {"status": "failed",
                              "errcode": '',
                              "error_message": u"创建es表失败"
                              }
                    }))
                Config.objects.filter(id=conf.id).update(
                    publish_status=config_status.FAILED)
                Host.objects.filter(config=conf).update(
                    status=host_exception
                )
                return

    Task.objects.filter(source_id=conf.id).update(
        status=json.dumps({
            "1": {"status": "success",
                  "errcode": "",
                  "error_message": ""
                  },
            "2": {"status": "working",
                  "errcode": "",
                  "error_message": ""
                  },
        }))

    # 开始下发配置
    try:
        publish_config_work(data_id_use, bk_token, ip_module, file_name, conf,
                            config_status, source, host_exception)
    except Exception,e:
        error_msg = u"下发采集器配置出现错误，错误信息%s" % e
        Task.objects.filter(source_id=conf.id).update(
            status=json.dumps({
                "1": {"status": "success",
                      "errcode": "",
                      "error_message": ""
                      },
                "2": {"status": "failed",
                      "errcode": "",
                      "error_message": error_msg
                      },
            }))
        conf.update(publish_status=config_status.FAILED)
        Host.objects.filter(conf_id=conf.id).update(status=host_exception)
    return


def publish_config_work(data_id_use, bk_token, ip_module, file_name, conf,
                        config_status, source, host_exception):
    """
    下发配置
    """
    push_config = deploy_collector(data_id_use, bk_token, ip_module, file_name,
                                   conf.app_id, conf.ex_files)

    # 解析下发配置结果，更新config、host、task三张表的状态
    config_status_str = Task.objects.filter(source_id=conf.id).values('status')
    config_status_dict = json.loads(config_status_str[0]['status'])

    push_config_data = []
    success_list = []
    failed_list = []
    if file_name:
        try:
            push_config_data = push_config["data"]
            success_list = push_config['data']['success']
            failed_list = push_config['data']['failed']
        except Exception, e:
            logger.error(u"获取返回结果错误，返回信息%s" % push_config)
    else:
        for item in push_config['data']:
            for each in item["success"]:
                success_list.append(each)

    if push_config['result'] and push_config['data'] and len(success_list) == len(ip_module):
        config_status_dict["2"] = {"status": "success",
                                   "errcode": "",
                                   "error_message": ""
                                   }
        Task.objects.filter(source_id=conf.id).update(
            status=json.dumps(config_status_dict))
        Config.objects.filter(id=conf.id).update(
            publish_status=config_status.SUCCESS)
        if file_name:
            for ip_data in push_config_data['success']:
                Host.objects.filter(ip=ip_data['obj']['ip']).update(
                    status=HostStatus.SUCCESS,
                )
            Host.objects.filter(
                ip__in=[ip_data_failed['obj']['ip'] for ip_data_failed in
                        push_config_data['failed']]).update(
                status=host_exception)
        else:
            for ip_data in push_config_data:
                for each in ip_data['success']:
                    Host.objects.filter(ip=each['obj']['ip']).delete()
        return
    else:
        config_status_dict["2"] = ({"status": "failed",
                                    "errcode": "",
                                    "error_message": ""
                                    })
        if success_list or failed_list:
            if source:
                Host.objects.filter(
                    ip__in=[ip_data_success['obj']['ip'] for ip_data_success in
                            success_list]).delete()
            else:
                Host.objects.filter(
                    ip__in=[ip_data_success['obj']['ip'] for ip_data_success in
                            success_list]).update(
                    status=HostStatus.SUCCESS)
            Host.objects.filter(
                ip__in=[ip_data_failed['obj']['ip'] for ip_data_failed in
                        failed_list]).update(
                status=host_exception)
            config_status_dict["2"]["error_message"] = push_config_data
        else:
            Host.objects.filter(
                ip__in=[item['ip'] for item in
                        ip_module]).update(
                status=host_exception)
            config_status_dict["2"]["error_message"] = u"返回结构异常"

        Task.objects.filter(source_id=conf.id).update(
            status=json.dumps(config_status_dict))
        Config.objects.filter(id=conf.id).update(
            publish_status=config_status.FAILED)
        return


def create_es(app_id, bk_token, data_id):
    """
    创建es
    @return:
    """
    set_result_table = trt_set_result_table(app_id, 'admin', bk_token)
    return set_result_table['result'] and add_es_connector(
        data_id,
        set_result_table['data']['result_table_id'],
        bk_token)


def get_data_id_api(app_id, user, bk_token):
    """
    @summary:创建data_id
    """
    request_create_data_id = copy.deepcopy(REQUEST_CREATE_DATA_ID)
    request_create_data_id.update({'bk_token': bk_token,
                                   'biz_id': app_id,
                                   'user': user,
                                   })
    url = BK_PAAS_HOST + "api/c/compapi/data/databus/create_data_id"
    try:
        result = requests.post(url, json.dumps(request_create_data_id),
                               headers=HEADERS, timeout=100)
        data = json.loads(result.text)
        if data['result']:
            data_id = DataId.objects.create(app_id=app_id,
                                            data_id=data['data']['data_id'])

            # 生成es表并添加es入库
            if create_es(app_id, bk_token, data['data']['data_id']):
                data_id.is_create_es = True
            else:
                logger.info(u"创建es表失败")
                data_id.is_create_es = False
                data['result'] = False
            data_id.save()
        return data
    except Exception as e:
        logger.error(u'获取API%s信息失败%s %s ' % (url, request_create_data_id, e))
        return {'result': False, 'code': 1,
                'message': 'failed to create data id!', 'data': []}


def trt_set_result_table(app_id, user, bk_token):
    """
    @summary:创建es表
    """
    request_result_table = copy.deepcopy(REQUEST_RESULT_TABLE)
    request_result_table['biz_id'] = app_id
    request_result_table['table_name'] = DATA_SET
    request_para = {
        'result_table': request_result_table,
        'committer': user,
        'app_code': APP_ID,
        'app_secret': APP_TOKEN,
        'bk_token': bk_token
    }
    url = BK_PAAS_HOST + 'api/c/compapi/data/trt/set_result_table'
    try:
        result = requests.post(url, json.dumps(request_para), headers=HEADERS, timeout=100)
        data = json.loads(result.text)
        return data
    except Exception as e:
        logger.error(u'获取API%s信息失败%s %s ' % (url, request_para, e))
        return {'result': False, 'data': []}


def add_es_connector(data_id, result_table_id, bk_token):
    """
    @summary:添加es入库
    """
    request_para = {
        'app_code': APP_ID,
        'app_secret': APP_TOKEN,
        'bk_token': bk_token,
        "data_id": data_id,
        "result_table_id": result_table_id,
    }
    url = BK_PAAS_HOST + 'api/c/compapi/data/databus/add_es_connector'
    try:
        result = requests.post(url, json.dumps(request_para), headers=HEADERS, timeout=100)
        data = json.loads(result.text)
        if data["result"]:
            return True
    except Exception as e:
        logger.error(u'add_es_connector 获取API%s信息失败%s %s ' % (
            url, request_para, e))
    return False


def deploy_collector(data_id, bk_token, hosts, files, app_id, ignore_file):
    """
    @summary:部署采集器接口
    """
    config_file = {
        "data_id": data_id,
        "app_secret": APP_TOKEN,
        "app_code": APP_ID,
        "bk_token": bk_token,
        "hosts": hosts,
        "files": files,
        "biz_id": app_id,
        "ignore_file_end_with": ignore_file,
        "conditions": []
    }
    if files:
        url = ('%sapi/c/compapi/data/databus/deploy_collector/'
               % BK_PAAS_HOST)
    else:
        url = ('%sapi/c/compapi/data/databus/stop_collector_by_dataid/'
               % BK_PAAS_HOST)
    try:
        result = requests.post(url, json.dumps(config_file), headers=HEADERS, timeout=100)
        data = json.loads(result.text)
        logger.info(u"下发采集器url:%s 返回信息%s"%(url, data))
        return data
    except Exception as e:
        logger.error(u'获取API%s信息失败%s %s ' % (url, config_file, e))
        return {'result': False,
                'data': [{'success': [],
                          'failed': [{'obj': host['ip']} for host in hosts],
                          'pending': []}]}


def query_host_result(app_id, host, bk_token):
    """
    @summary:后台轮询主机状态（只有当前主机状态为“成功”时才轮询）
    """
    # 调用下发查询接口
    ip = host.ip
    REQUEST_GET_PRO_STATUS.update({'app_code': APP_ID, 'app_secret': APP_TOKEN, 'app_id': app_id,
                                   'bk_token': bk_token})
    REQUEST_GET_PRO_STATUS['proc_list'][0]['ip_list'][0]['ip'] = ip
    hosts = get_ip_by_app(app_id, bk_token)
    plat_id = ''
    for each in hosts:
        if each["InnerIP"] == host.ip and each["ModuleName"] == host.module:
            plat_id = each["Source"]
    REQUEST_GET_PRO_STATUS['proc_list'][0]['ip_list'][0]['source'] = plat_id
    url = BK_PAAS_HOST + 'api/c/compapi/job/gse_proc_operate/'
    result = requests.post(url, json.dumps(REQUEST_GET_PRO_STATUS),
                           headers=HEADERS, timeout=100)
    data = json.loads(result.text)

    # 轮询次数，防止死循环
    flag = 0

    # 调用获取查询结果的接口，并修改主机状态
    while True:
        flag += 1
        try:
            config_status_result = get_get_proc_rst(app_id, data['data']['gseTaskId'],
                                                    bk_token)
            config_status = config_status_result['errcode']
        except Exception as e:
            logger.error(u'获取主机状态失败%s ' %  e)
            host.status = HostStatus.STATUS_EXCEPTION
            break
        if config_status == 0:
            host.status = HostStatus.COLLECTING
            break
        else:
            host.status = HostStatus.STATUS_EXCEPTION
        if config_status != 115:
            break
        if flag == 15:
            logger.warning(u"轮询主机状态时死循环%s" % config_status_result)
            break
        time.sleep(0.1)
    host.is_get_status = False
    host.save()


def get_get_proc_rst(app_id, task_id, bk_token):
    """
    @summary:获取主机状态查询结果
    """
    request_para = {
        "app_code": APP_ID,
        "app_secret": APP_TOKEN,
        "bk_token": bk_token,
        "username": "admin",
        "app_id": app_id,
        "gse_task_id": task_id
    }
    url = BK_PAAS_HOST + 'api/c/compapi/job/get_proc_result/'
    result = requests.post(url, json.dumps(request_para), headers=HEADERS, timeout=100)
    data = json.loads(result.text)
    if data['data'] and data['result']:
        errcode = data['data'].values()
        msg_use = errcode[0].values()
        return {'result': True, 'errcode': msg_use[0]['errcode'],
                'error_message': msg_use[0]['errmsg']}
    else:
        return {'result': False, 'errcode': data['code']}


def get_collecting_ips(data, bk_token):
    """
    获取现在运行的采集项数量
    """
    ip_list = []
    if data['ips_source'] == '1':
        ip_list = data['ips']

    if data['ips_source'] == '0':
        module_list = data["modules"].split(",")
        ip_list = []
        hosts = get_ip_by_app(data["app_id"], bk_token)

        for module in module_list:
            ip_data = get_ip_by_module(hosts, module)
            for ip in ip_data:
                ip_list.append(ip["InnerIP"])

    ips = Host.objects.filter(ip__in=ip_list).values('ip')
    total = ips.count()
    ip_data = [ip['ip'] for ip in ips]
    return True, total, ip_data


def es_chart(app_id, bk_token, keyword, date_inteval="day", date_start=None, date_end=None,condition={}):
    """
    condition为预留字段
    获取以一定时间频率为间隔聚合统计的图表数据
    @return:
    """
    inteval = date_inteval
    timetaken = 0
    index = "%s_%s_%s*" % (app_id, DATA_SET, datetime.datetime.now().year)

    body_dict = {
        "aggs": {
            "time_aggs": {
                "date_histogram": {
                    "field": "tagTime",
                    "interval": inteval,
                    "time_zone": "+08:00"
                }
            }
        }
    }
    key_list = keyword.split(' ')
    query_list = []

    # 包含特殊字符则不加通配符，否则拿通配符包裹
    for query_key in key_list:
        if not query_key:
            continue
        pattern = "%s" if check_special_string(query_key) else "*%s*"
        # escaped_str = ""
        # for tmp_str in query_key:
        #     if tmp_str in ['!', ':', '/', '\\', '[', ']', '?', '&', '-', '{', '}', '>', '<']:
        #         escaped_str += "\\"
        #     escaped_str += tmp_str

        query_list.append(pattern % query_key)

    query_str = ' '.join(query_list)
    if keyword:
        body_dict.update({"query": {
            "query_string": {
                "fields": ["log", "serverIp", "moduleName", "localTime"],
                "lenient": True,
                "query": query_str,
                "analyze_wildcard": True,
            },
        }})
    request_para = {
        'app_code': APP_ID,
        'app_secret': APP_TOKEN,
        'bk_token': bk_token,
        'prefer_storage': "es",
        'sql': json.dumps({'index': index, 'body': body_dict}),
    }
    url = '%sapi/c/compapi/data/maple/get_data/' % BK_PAAS_HOST

    try:
        result = requests.post(url, json.dumps(request_para), headers=HEADERS, timeout=100)
        text = json.loads(result.text)
        search_result = text['data']['list']
        timetaken = text['data']['timetaken']
    except Exception as e:
        logger.error(u'查询过程出现错误：%s' % e)
        return [], "day", timetaken
    chart_data = []
    for item in search_result['aggregations']['time_aggs']['buckets']:
        chart_data.append([item['key'], item['doc_count']])

    if inteval.endswith('m'):
        inteval = inteval[0:-1] + ' minutes'

    if inteval.endswith('h'):
        inteval = inteval[0:-1] + ' hours'

    return chart_data, inteval, round(timetaken, 2)


def form_excel(data):
    """
    生成excel
    """
    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet(u"日志数据")

    field_list = ['localTime', 'log', 'moduleName', 'serverIp', 'tagTime']

    for idx, item in enumerate(data['log_list']):
        column = 0
        for field in field_list:
            deal_data = unicode(item[field])
            sheet.write(idx + 1, column, deal_data)
            column += 1

    return wbk


def create_period_task(task_params, register_task, task_name):
    '''
    @summary：创建周期性任务
    '''
    execute_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
    task, created = PeriodicTask.objects.get_or_create(name=task_name)
    task.task = register_task
    task.kwargs = json.dumps(task_params)
    task.save()
    if created:
        crontab = CrontabSchedule.objects.create(minute=execute_time.minute,
                                                 hour=execute_time.hour,
                                                 day_of_week="*",
                                                 day_of_month=execute_time.day,
                                                 month_of_year=execute_time.month,
                                                 )
        crontab.save()
        task.crontab = crontab
        task.enabled = True
        task.save()
    return True


@task(ignore_result=True)
def clean_timeout_task(conf_id, host_exception):
    '''
    @summary：超时任务数据库更新
    '''
    # 当前针对的conf需要删除清理
    if Config.objects.filter(id=conf_id, publish_status=ConfigStatus.WORKING).exists():
        Task.objects.filter(source_id=conf_id).update(
            status=json.dumps({
                "1": {"status": "success",
                      "errcode": "",
                      "error_message": ""
                      },
                "2": {"status": "failed",
                      "errcode": "",
                      "error_message": u"任务超时"
                      },
            }))
        Config.objects.filter(id=conf_id, publish_status=ConfigStatus.WORKING).update(
            publish_status=ConfigStatus.FAILED)
    Host.objects.filter(config_id=conf_id, status__in=[HostStatus.RELEASING, HostStatus.REMOVING, HostStatus.WAITING]).update(status=host_exception)

    # 历史上超过5分钟的数据也需要清除
    history_timeout_config = Config.objects.filter(publish_status=ConfigStatus.WORKING,
                             publish_time__lte = datetime.datetime.now() - datetime.timedelta(minutes=5))
    if history_timeout_config.exists():
        history_timeout_config.update(publish_status=ConfigStatus.FAILED)
        history_timeout_config_ids =history_timeout_config.values_list("id")
        Task.objects.filter(source_id__in=history_timeout_config_ids).update(
            status=json.dumps({
                "1": {"status": "success",
                      "errcode": "",
                      "error_message": ""
                      },
                "2": {"status": "failed",
                      "errcode": "",
                      "error_message": u"任务超时"
                      },
            }))
        Host.objects.filter(config_id__in=history_timeout_config_ids).update(status=HostStatus.STATUS_EXCEPTION)
    # 删除周期任务
    try:
        PeriodicTask.objects.get(name="clean_timeout_task_%s" % conf_id).delete()
    except:
        pass

