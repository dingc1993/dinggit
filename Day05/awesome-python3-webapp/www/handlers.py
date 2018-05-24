# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/24 16:21
"""

from www.coroweb import get,post
import asyncio

#编写用于测试的URL处理函数
@get('/')
async def handler_url_blog():
    body='<h1>Awesome</h1>'
    return body

@get('/greeting')
async def handler_url_greeting(*,name):
    body='<h1>Awesome: /greeting %s</h1>'%name
    return body