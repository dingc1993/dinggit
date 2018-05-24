# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/23 16:33
"""
from www.orm import Model, StringField, IntegerField,create_pool,destory_pool
import asyncio
import sys
from www.models import User

# 创建User对象用于封装相关信息（类似于javaweb中的domain）

def main():
    class User(Model):
        id = IntegerField('id', primary_key=True)
        name = StringField('username')

    # 创建实例
    @asyncio.coroutine
    def test(loop):
        yield from create_pool(loop=loop, host='localhost', port=3306, user='root', password='root', db='awesome')
        # user = User(id=1, name='ding')
        # yield from user.save()
        r = yield from User.find('1')
        print(r)
        yield from destory_pool()
    # loop:消息循环
    # 创建异步事件的句柄
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
    if loop.is_closed():
        sys.exit(0)

loop = asyncio.get_event_loop()
# 编写数据访问代码
async def test():
    await create_pool(loop=loop,host='localhost', port=3306,user='root',password='root',db='awesome')

    u = User(username='ding1',password='1234',email='ding1@sina.com',image='about_blank')

    try:
        await u.save()
        await destory_pool()
    except Exception as e:
        raise RuntimeError(e.__context__)

if __name__ == "__main__":
    # main()
    loop.run_until_complete(test())
    loop.close()
    if loop.is_closed():
        sys.exit(0)