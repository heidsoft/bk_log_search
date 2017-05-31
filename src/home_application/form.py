# -*- coding: utf-8 -*-
import re

from django import forms

from utils import html_decode


class SearchLogForm(forms.Form):
    size = forms.IntegerField(label=u"分页长度")
    start = forms.IntegerField(label=u"分页起始位")
    app_id = forms.IntegerField(label=u"app_id")
    key = forms.CharField(label=u"关键词", required=False)

    def clean_key(self):
        if 'key' in self.cleaned_data:
            key = self.cleaned_data['key']
            return html_decode(key)
        else:
            return ''


class HistogramLogForm(forms.Form):
    app_id = forms.IntegerField(label=u"app_id")
    keyword = forms.CharField(label=u"关键词", required=False)
    date_start = forms.DateTimeField(label=u"起始时间", required=False)
    date_end = forms.DateTimeField(label=u"结束时间", required=False)
    date_inteval = forms.CharField(label=u"聚合粒度", required=False)
    condition = forms.CharField(label=u"其他条件", required=False)

    def clean_key(self):
        if 'keyword' in self.cleaned_data:
            keyword = self.cleaned_data['keyword']
            return html_decode(keyword)
        else:
            return ''


def check_ip(ip):
    """
    检查IP合法性
    @param ip:
    @return:
    """
    ip = re.match(r'^\d+\.\d+\.\d+\.\d+$', ip)
    if ip is None:
        return False
    match_result = [0 <= int(x) < 256 for x in re.split('\.', ip.group(0))]
    check_result = match_result.count(True) == 4
    return check_result


class ConfigForm(forms.Form):
    modules = forms.CharField(label=u"模块", required=False)
    ips = forms.CharField(label=u"IP", required=False)
    ips_source = forms.ChoiceField(label=u"IP来源",
                                   choices=(('0', u"模块"),
                                            ('1', u"手动输入")))
    app_id = forms.IntegerField(label=u"app_id")
    paths = forms.CharField(label=u"路径", )
    ex_files = forms.CharField(label=u"排除文件", required=False)

    def clean_ips(self):
        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if 'ips' not in self.cleaned_data:
            return []
        ip = self.cleaned_data['ips']
        ip_list = list(set(pat.findall(ip)))

        result_list = []
        for ip in ip_list:
            if check_ip(ip):
                result_list.append(ip)
        return result_list

    def clean_paths(self):
        paths = filter(None, set(self.cleaned_data['paths'].split(',')))
        for path in paths:
            if path and path[-1] == '/':
                raise forms.ValidationError(u"path结尾不得为/")
            if path and path[0] != '/':
                raise forms.ValidationError(u"path需填写绝对路径")
        return ','.join(paths)

    def clean_ips_source(self):
        form = self.cleaned_data
        ips = form['ips'] or ''
        modules = form['modules'] or ''
        ips_source = form['ips_source']
        if form['ips_source'] == '1' and not ips:
            raise forms.ValidationError(u"ip 不能为空")
        if form['ips_source'] == '0' and not modules:
            raise forms.ValidationError(u"modules 不能为空")

        return ips_source


class QueryForm(forms.Form):
    length = forms.IntegerField(label=u"长度")
    offset = forms.IntegerField(label=u"起始位")
    app_id = forms.IntegerField(label=u"app_id")
    value = forms.CharField(label=u"搜索字段", required=False)
    sort_method = forms.ChoiceField(label=u"排序方法",
                                    choices=(('desc', u"倒序"),
                                             ('asc', u"正序")),
                                    required=False)
    sort = forms.CharField(label=u"排序字段", required=False)

    def clean_sort(self):
        if 'sort_method' in self.cleaned_data:
            sort_method = self.cleaned_data['sort_method']
        else:
            sort_method = 'desc'

        sort = self.cleaned_data['sort']

        if sort_method == 'desc':
            return "-%s" % sort
        else:
            return sort


class CheckPublishIpsForm(forms.Form):
    modules = forms.CharField(label=u"模块", required=False)
    ips = forms.CharField(label=u"IP", required=False)
    app_id = forms.IntegerField(label=u"app_id")
    ips_source = forms.ChoiceField(label=u"IP来源",
                                   choices=(('0', u"模块"), ('1', u"手动输入")))

    def clean_ips(self):
        pat = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if 'ips' not in self.cleaned_data:
            return []
        ip = self.cleaned_data['ips']
        ip_list = list(set(pat.findall(ip)))

        result_list = []
        for ip in ip_list:
            if check_ip(ip):
                result_list.append(ip)
        return result_list

    def clean_ips_source(self):
        form = self.cleaned_data
        ips = form['ips'] or ''
        modules = form['modules'] or ''
        ips_source = form['ips_source']
        if form['ips_source'] == '1' and not ips:
            raise forms.ValidationError(u"ip 不能为空")
        if form['ips_source'] == '0' and not modules:
            raise forms.ValidationError(u"modules 不能为空")

        return ips_source