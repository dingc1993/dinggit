# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/24 15:51
"""
from aiohttp import web
from www.app import init_jinja2,datetime_filter
from www.middleware import logger_factory,response_factory
from www.coroweb import add_routes,add_static
import logging,asyncio
from www import orm


#编写web框架测试
async def init(loop):
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='root', password='root', db='awesome')
    app = web.Application(loop=loop,middlewares=[logger_factory,response_factory])
    init_jinja2(app,filters=dict(datetime=datetime_filter))#初始化Jinja2，这里值得注意是设置文件路径的path参数
    #同级目录不需要添加相应的模块信息
    add_routes(app,'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('Server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()