# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/22 16:38
"""

# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/21 21:03
"""
import logging
logging.basicConfig(level=logging.INFO)
# 一次使用异步 处处使用异步
import asyncio,os,time,random
from datetime import datetime
from aiohttp import web
import aiomysql
import sys
##那aiohttp是什么鬼aiomysql。他们都是基于asyncore实现的异步http库异步mysql库调用他们就可以实
#现异步请求在http和mysql上。记住：一处异步 处处异步


####二.实现ORM
'''
相关介绍：
由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。在协程中，不能调用普通的同步IO操作，因为所有用户
都是由一个线程服务的，协程的执行速度必须非常快，才能处理大量用户的请求。而耗时的IO操作不能在协程中以同步的方式
调用，否则，等待一个IO操作时，系统无法响应任何其他用户。

这就是异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步，“开弓没有回头箭”。
幸运的是aiomysql为MySQL数据库提供了异步IO的驱动。
'''

def log(sql, args=()):
    logging.info('SQL: %s' % sql)

#Close pool
async def destory_pool():
     global __pool
     __pool.close()
     await __pool.wait_closed()

 #Create connect pool
 #Parameter: host,port,user,password,db,charset,autocommit
 #           maxsize,minsize,loop
##创建连接池
#创建一个全局的连接池，每个HTTP请求都从池中获得数据库连接
#连接池由全局变量__pool存储，缺省情况下将编码设置为utf8，自动提交事务
@asyncio.coroutine
def create_pool(loop,**kw):#charset参数是utf8
    logging.info(r'Create database connection pool...')
    #定义全局变量__pool用于存储所有连接池对象
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host','localhost'),
        port=kw.get('port','3306'),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        #消息循环控制
        loop=loop
    )#创建连接所需要的参数

##执行SELECT语句
#Package SELECT function that can execute SELECT command.
#Setup 1:acquire connection from connection pool.
#Setup 2:create a cursor to execute MySQL command.
#Setup 3:execute MySQL command with cursor.
#Setup 4:return query result.
#（传入sql语句+args参数信息+关键字（可变））
#单独封装select，其他insert,update,delete一并封装，理由如下：
#使用Cursor对象执行insert，update，delete语句时，执行结果由rowcount返回影响的行数，就可以拿到执行结果。
#使用Cursor对象执行select语句时，通过featchall()可以拿到结果集。结果集是一个list，每个元素都是一个tuple，对应一行记录。
@asyncio.coroutine
def select(sql,args,size=None):
    log(sql,args)
    global __pool
    # 666 建立游标
    # -*- yield from 将会调用一个子协程，并直接返回调用的结果
    # yield from从连接池中返回一个连接
    with (yield from __pool) as conn:#打开pool的方法,或-->async with __pool.get() as conn:
        #获取游标cursor对象
        # 创建游标,aiomysql.DictCursor的作用使生成结果是一个dict
        cur = yield from conn.cursor(aiomysql.DictCursor)
        # 执行sql语句，sql语句的占位符是'?',而Mysql的占位符是'%s'
        yield from cur.execute(sql.replace('?','%s'),args or ())
        if size:
            #通过外部控制返回的结果数量（size）
            rs = yield from cur.fetchmany(size)
        else:
            #通过fetchall方法获取所有查询结果
            rs = yield from cur.fetchall()
        #关闭cursor游标
        yield from cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

'''
SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。注意要始终坚持使用带参数的SQL，
而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。(javaweb也有相应形式)
注意到yield from将调用一个子协程（也就是在一个协程中调用另一个协程）并直接获得子协程的返回结果。
如果传入size参数，就通过fetchmany()获取最多指定数量的记录，否则，通过fetchall()获取所有记录。
'''

##Insert, Update, Delete
##要执行INSERT、UPDATE、DELETE语句，可以定义一个通用的execute()函数，因为这3种SQL的执行都需要相同的参数，
##以及返回一个整数表示影响的行数：
@asyncio.coroutine
def execute(sql, args,autocommit=True):
    log(sql)
    with (yield from __pool) as conn:
        if not autocommit:
            # python中连接对象开始一个事务的方法（开启事务，autocommit=false，start transaction：开启事务）
            yield from conn.begin()
        try:
            # 因为execute类型sql操作返回结果只有行号，不需要dict
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args)
            #获取影响的行数
            affected = cur.rowcount
            # 如果MySQL禁止隐式提交，手动提交事务
            if not autocommit:
                yield from conn.commit()
        # 如果事务处理出现错误，则回退
        except BaseException as e:
            #如果出现异常，则事务回滚
            yield from conn.rollback()
            raise

        return affected
#execute()函数和select()函数所不同的是，cursor对象不返回结果集，而是通过rowcount返回结果数。

# 这个函数主要是把查询字段计数替换成sql识别的?
# 比如说：insert into  `User` (`password`, `email`, `name`, `id`) values (?,?,?,?)
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


##ORM
#有了基本的select()和execute()函数，我们就可以开始编写一个简单的ORM了。
#设计ORM需要从上层调用者角度来设计。
#我们先考虑如何定义一个User对象，然后把数据库表users和它关联起来
####定义Field
##首先要定义的是所有ORM映射的基类Model：
# 定义Field类，负责保存(数据库)表的字段名和字段类型
class Field(object):
    # 表的字段包含名字、类型、是否为表的主键和默认值
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        # 返回 表名字 字段名 和字段类型
        return '<%s,%s:%s>'%(self.__class__.__name__,self.column_type,self.name)
    __repr__ = __str__

#定义一个StringField对象
# 定义数据库中五个存储类型
class StringField(Field):
    def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)

# 布尔类型不可以作为主键
class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

# Meatclass about ORM
# 作用：
# 首先，拦截类的创建
# 然后，修改类
# 最后，返回修改后的类
#Model只是一个基类，如何将具体的子类如User的映射信息读取出来呢？答案就是通过metaclass：ModelMetaclass：

# class Model(dict,metaclass=ModelMetaclass):

# -*-定义Model的元类
# 所有的元类都继承自type
# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作
# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：
# ***读取具体子类(user)的映射信息
# 创造类的时候，排除对Model类的修改
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除
# Field(防止实例属性遮住类的同名属性)
# 将数据库表名保存到__table__中
# 完成这些工作就可以在Model中定义各种数据库的操作方法
# metaclass是类的模板，所以必须从`type`类型派生：
class ModelMetaClass(type):
    # 采集应用元类的子类属性信息
    # 将采集的信息作为参数传入__new__方法
    # 应用__new__方法修改类

    # __new__控制__init__的执行，所以在其执行之前
    # cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)
    # bases：代表继承父类的集合
    # attrs：类的方法集合
    def __new__(cls, name,bases, attrs):#当前准备创建的类的对象；类的名字；类继承的父类集合；类的方法集合。
        # 排除Model类本身:是因为要排除对model类的修改
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)
        # 获取table名称:
        # 获取数据库表名。若__table__为None,则取用类名
        tablename = attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name,tablename))
        # 获取所有的Field和主键名:
        mappings = dict()#保存映射关系
        fields = []#保存除主键外的属性
        # 主键对应字段
        primaryKey = None
        for k,v in attrs.items():
            if isinstance(v,Field):
                logging.info(' found mapping: %s ==> %s' % (k,v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k#此列设为列表的主键
                else:
                    fields.append(k)#保存除主键外的属性
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        #清空attrs集合对象中的相关数据信息
        for k in mappings.keys():
            # 删除映射表类的属性，以便应用新的属性
            attrs.pop(k)#从类属性中删除Field属性,否则，容易造成运行时错误（实例的属性会遮盖类的同名属性）
        # 使用反单引号" ` "区别MySQL保留字，提高兼容性
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))#转换为sql语法
        # 创建供Model类使用属性
        attrs['__mappings__'] = mappings #保存属性和列的映射关系
        attrs['__table__'] = tablename #封装表名
        attrs['__primary_key__'] = primaryKey#存储主键信息
        attrs['__fields__'] = fields#封装除了主键以外的所有属性信息
        #构造默认的SELECT,INSERT,UPDATE,DELETE语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tablename)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
        tablename, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
        tablename, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tablename, primaryKey)
        return type.__new__(cls, name, bases, attrs)

#定义Model
#首先要定义的是所有ORM映射的基类Model：
class Model(dict,metaclass=ModelMetaClass):
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)

    #Model从dict继承，所以具备所有dict的功能，同时又实现了特殊方法__getattr__()和__setattr__()
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        #直接调回内置函数，注意这里没有下划符,注意这里None的用处,是为了当user没有赋值数据时，返回None，调用于update
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        # 第三个参数None，可以在没有返回数值时，返回None，调用于save
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                # __call__()的作用是使实例能够像函数一样被调用，同时不影响实例本身的生命周期（__call__()
                # 不影响一个实例的构造和析构）。但是__call__()可以用来改变实例的内部成员的值。
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    # ORM框架下，每条记录作为对象返回
    # @classmethod定义类方法，类对象cls便可完成某些操作
    # 类方法有类变量cls传入，从而可以用cls做一些相关的处理。并且有子类继承时，调用该类方法时，
    # 传入的类变量cls是子类(User)，而非父类。
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        ' find objects by where clause. '
        sql = [cls.__select__]
        # 添加WHERE子句
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        # 添加ORDER BY子句
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        # 添加LIMIT子句
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        # execute SQL
        rs = await select(' '.join(sql), args)
        # 将每条记录作为对象返回
        return [cls(**r) for r in rs]

    # 过滤结果数量
    # findNumber()-根据WHERE条件查找，但返回的是整数，适用于select count(*)类型的SQL。
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        # 添加WHERE子句
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    # 返回主键的一条记录
    @classmethod
    async def find(cls, pk):
        ' find object by primary key. '
        #通过主键查询结果集对象
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)

if __name__ == "__main__":
    #创建User对象用于封装相关信息（类似于javaweb中的domain）
    class User(Model):
        id = IntegerField('id', primary_key=True)
        name = StringField('username')

    #loop:消息循环
    # 创建异步事件的句柄
    loop = asyncio.get_event_loop()


    # 创建实例
    @asyncio.coroutine
    def test():
        yield from create_pool(loop=loop, host='localhost', port=3306, user='root', password='root', db='awesome')
        # user = User(id=1, name='ding')
        # yield from user.save()
        r = yield from User.find('1')
        print(r)
        #关闭eventloop之前首先关闭连接池
        yield from destory_pool()

    loop.run_until_complete(test())
    loop.close()
    if loop.is_closed():
        sys.exit(0)
