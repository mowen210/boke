# -*- coding: utf-8 -*-
"""自定义异常与全局异常语义。"""


class PageLoginRequired(Exception):
    """页面访问未登录。

    由 main.py 中注册的全局异常处理器捕获，重定向到登录页 /login，
    实现“未登录访问首页、详情页自动跳转登录页”。
    """
