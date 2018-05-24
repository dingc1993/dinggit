# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/23 18:56
"""
import asyncio
import functools
import logging
import os

####四.编写Web框架

##在正式开始Web开发前，我们需要编写一个Web框架。
##aiohttp已经是一个Web框架了，为什么我们还需要自己封装一个？
##原因是从使用者的角度来说，aiohttp相对比较底层，编写一个URL的处理函数需要这么几步：

###1. 编写URL处理函数
##1.1 aiohttp编写URL处理处理函数
'''
#第一步，编写一个用@asyncio.coroutine装饰的函数：
@asyncio.coroutine
def handle_url_xxx(request): #url处理函数(传入request对象)
    pass

#第二步，传入的参数需要自己从request中获取：
url_param = request.match_info['key'] #url参数
query_params = parse_qs(request.query_string) #查询参数

#最后，需要自己构造Response对象：
text = render('template', data)
return web.Response(text.encode('utf-8'))
#这些重复的工作可以由框架完成。例如，处理带参数的URL/blog/{id}可以这么写：

@get('/blog/{id}')
def get_blog(id):
    pass
# 处理query_string参数可以通过关键字参数**kw或者命名关键字参数接收：

@get('/api/comments')
def api_comments(*, page='1'):
    pass
# 对于函数的返回值，不一定是web.Response对象，可以是str、bytes或dict。
# 如果希望渲染模板，我们可以这么返回一个dict：
return {
    '__template__': 'index.html',
    'data': '...'
}
# 因此，Web框架的设计是完全从使用者出发，目的是让使用者编写尽可能少的代码。
# 编写简单的函数而非引入request和web.Response还有一个额外的好处，就是可以单独测试，否则，需要模拟一个request才能测试。
'''

##1.2 新建web框架编写URL处理函数
#1.2.1 @get和@post
#1.要把一个函数映射为一个URL处理函数，我们先定义@get()：
#func = get('/path')(func)
# def get(path):
#     '''
#     Define decorator @get('/path')
#     '''
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args,**kw):
#             return func(*args,**kw)
#         #为wrapper函数添加属性信息
#         wrapper.__method__ = 'GET'
#         wrapper.__route__ = path
#         return wrapper #返回函数对象
#     return decorator
#
# def post(path):
#     '''
#     Define decorator @post('/path')
#     '''
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args,**kw):
#             return func(*args,**kw)
#         wrapper.__method__ = 'POST'
#         wrapper.__route__ = path
#         return wrapper
#     return decorator

#这里运用偏函数，一并建立URL处理函数的装饰器，用来存储GET、POST和URL路径信息
import functools
def Handler_decorator(path,*,method):
    def decorator(func):
        @functools.wraps(func)#更正函数签名
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__route__ = path #存储路径信息,注意这里属性名叫route
        wrapper.__method__ = method #存储方法信息
        return wrapper
    return decorator

get = functools.partial(Handler_decorator,method = 'GET')
post = functools.partial(Handler_decorator,method = 'POST')

import inspect
from aiohttp import web
from urllib import parse
from www.apis import APIError


#运用inspect模块，创建几个函数用以获取URL处理函数与request参数之间的关系
#1.获取没有默认值的命名关键字参数
def get_required_kw_args(fn):
    '''
       名称	                                            含义
    POSITIONAL_ONLY	              必须为位置参数，python没有明确定义位置参数的语法
    POSITIONAL_OR_KEYWORD	                可以为位置参数或者关键字参数
    VAR_POSITIONAL	        位置参数的元素没有绑定到任何其他参数，对应python函数定义中的*args（可变参数）
    KEYWORD_ONLY	   值必须作为关键字参数提供,只有关键字参数是指出现在*或者*args之后的参数（命名关键字参数）
    VAR_KEYWORD	         没有绑定到任何其他参数的关键字参数的字典，对应参数定义的**kwargs（关键字参数）
    '''
    args = []
    # inspect模块是用来分析模块，函数
    params = inspect.signature(fn).parameters
    #通过调用items方法实现迭代操作
    for name,param in params.items():
        #通过kind属性判断key关键字类型是否是命名关键字
        if param.kind ==  inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

#2.获取命名关键字参数
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind ==  inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

#3.判断有没有命名关键字参数
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind ==  inspect.Parameter.KEYWORD_ONLY:
            return True
        else:
            return False

#4.判断有没有关键字参数
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
        else:
            return False

#5.判断是否含有名叫'request'参数，且该参数是否为最后一个参数
def has_request_arg(fn):
    params = inspect.signature(fn).parameters
    sig = inspect.signature(fn)
    found = False
    for name,param in params.items():
        if name == 'request':
            found = True
            continue #跳出当前循环，执行下次循环
            if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
                raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
        return found

#1.2.3 定义RequestHandler
#URL处理函数不一定是一个coroutine，因此我们用RequestHandler()来封装一个URL处理函数。
#RequestHandler是一个类，由于定义了__call__()方法，因此可以将其实例视为函数。
#RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数，然后把结果转换为
#web.Response对象，这样，就完全符合aiohttp框架的要求：
class RequestHandler(object):##类似于javaweb中的servlet处理相应的请求信息

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        # 是否具有request参数，且该参数是否为最后一个参数
        self._has_request_arg = has_request_arg(fn)
        # 是否具有关键字参数
        self._has_var_kw_arg = has_var_kw_arg(fn)
        # 是否具有命名关键字参数
        self._has_named_kw_args = has_named_kw_args(fn)
        # 命名关键字参数
        self._named_kw_args = get_named_kw_args(fn)
        # 不含默认值的命名关键字的参数
        self._required_kw_args = get_required_kw_args(fn)

    # 实现__call__方法
    async def __call__(self, request):#通过协程进行操作
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            # 判断请求方式是否为POST
            if request.method == 'POST':#判断客户端的请求方式是否为POST
                if not request.content_type:#查询有没提交数据的格式（EncType）
                    return web.HTTPBadRequest(text='Missing Content-Type.')
                ct = request.content_type.lower()
                # 判断是否是json类型
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):#Read request body decoded as json.
                        return web.HTTPBadRequest(text='JSON body must be object.')
                    kw = params
                    # form的enctype属性为编码方式，常用有两种：application/x-www-form-urlencoded和multipart/form-data，
                    # 默认为application/x-www-form-urlencoded。
                    # 1.x-www-form-urlencoded当action为get时候，浏览器用x-www-form-urlencoded的编码方式把form数据转换成
                    # 一个字串（name1=value1&name2=value2…），然后把这个字串append到url后面，用?分割，加载这个新的url。
                    # 2.multipart/form-data当action为post时候，浏览器把form数据封装到http body中，然后发送到server。
                    # 如果没有type=file的控件，用默认的application/x-www-form-urlencoded就可以了。 但是如果有type=file
                    # 的话，就要用到multipart/form-data了。浏览器会把整个表单以控件为单位分割，并为每个部分加上Content-
                    # Disposition(form-data或者file),Content-Type(默认为text/plain),name(控件name)等信息，并加上分割符
                    # (boundary)。

                    # reads POST parameters from request body.If method is not POST, PUT, PATCH, TRACE or DELETE or
                    # content_type is not empty or application/x-www-form-urlencoded or multipart/form-data returns empty multidict.
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(text='Unsupported Content-Type: %s' % request.content_type)
            # 判断请求方式是否为GET
            if request.method == 'GET':
                qs = request.query_string#The query string in the URL
                if qs:
                    kw = dict()
                    # Parse a query string given as a string argument.Data are returned as a dictionary. The
                    # dictionary keys are the unique query variable names and the values are lists of values for
                    # each name.
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        # check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest(text='Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

###2. 编写add_route函数以及add_static函数
'''
由于新建的web框架时基于aiohttp框架，所以需要再编写一个add_route函数，用来注册一个URL处理函数，主要起验证函数
是否有包含URL的响应方法与路径信息，以及将函数变为协程。
'''
#编写一个add_route函数，用来注册一个URL处理函数
def add_route(app,fn):
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__route__',None)
    if method is None or path is None:
        return ValueError('@get or @post not defined in %s.'%str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn): #判断是否为协程且生成器,不是使用isinstance
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)'%(method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))#别忘了RequestHandler的参数有两个

#通常add_route()注册会调用很多次，而为了框架使用者更加方便，可以编写了一个可以批量注册的函数，预期效果是：只需向这个函数提供
#要批量注册函数的文件路径，新编写的函数就会筛选，注册文件内所有符合注册条件的函数。
def add_routes(app,module_name):
    '''
    返回'.'最后出现的位置
    如果为-1，说明是 module_name中不带'.',例如(只是举个例子) handles 、 models
    如果不为-1,说明 module_name中带'.',例如(只是举个例子) aiohttp.web 、 urlib.parse()    n分别为 7 和 5
    我们在app中调用的时候传入的module_name为handles,不含'.',if成立, 动态加载module
    '''
    '''
    Python rfind() 返回字符串最后一次出现的位置(从右向左查询)，如果没有匹配项则返回-1。
    str.rfind(str, beg=0 end=len(string))
    str -- 查找的字符串
    beg -- 开始查找的位置，默认为 0
    end -- 结束查找位置，默认为字符串的长度。
    '''
    n = module_name.rfind('.')
    # n=-1,说明module_name中不含'.',动态加载该module
    if n == -1:
        '''
        __import__() 函数用于动态加载类和函数 。
        如果一个模块经常变化就可以使用 __import__() 来动态载入。
        '''
        mod = __import__(module_name, globals(), locals()) #加载handlers模块
    # n!=-1 module_name中存在'.'
    else:
        ''' 
        比如 aaa.bbb 类型,我们需要从aaa中加载bbb 
        n = 3 
        name = module_name[n+1:] 为bbb 
        module_name[:n] 为aaa     
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)，动态加载aaa.bbb 
        上边三句其实相当于： 
            aaa = __import__(module_name[:n], globals(), locals(), ['bbb']) 
            mod = aaa.bbb 
        还不明白的话看官方文档,讲的特别清楚： 
        https://docs.python.org/3/library/functions.html?highlight=__import__#__import__ 
        '''
        name = module_name[n + 1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    # for循环把所有的url处理函数给注册了
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            # 注册url处理函数fn，如果不是url处理函数,那么其method或者route为none，自然也不会被注册
            if method and path:
                add_route(app, fn)# 这里要查询path以及method是否存在而不是等待add_route函数查询，因为那里错误就要报错了


#添加静态文件夹的路径：
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')  # 输出当前文件夹中'static'的路径
    app.router.add_static('/static/', path)  # prefix (str) – URL path prefix for handled static files
    logging.info('add static %s => %s' % ('/static/', path))