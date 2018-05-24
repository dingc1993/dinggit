# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/23 17:01
"""

####python中的自定义异常
class DatabaseException(Exception):
    def __int__(self,err='数据库错误！！'):
        # super(DatabaseException,self).__init__(err)
        Exception.__init__(self,err)

class SQLException(DatabaseException):
    def __int__(self,err='SQLException'):
        DatabaseException.__init__(self,err)