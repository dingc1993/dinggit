# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/23 20:45
"""

'''
inspect.signature（fn)将返回一个inspect.Signature类型的对象，值为fn这个函数的所有参数
inspect.Signature对象的paramerters属性是一个mappingproxy（映射）类型的对象，值为一个有序字典（Orderdict)。
    这个字典里的key是即为参数名，str类型
    这个字典里的value是一个inspect.Parameter类型的对象，根据我的理解，这个对象里包含的一个参数的各种信息
inspect.Parameter对象的kind属性是一个_ParameterKind枚举类型的对象，值为这个参数的类型（可变参数，关键词参数，etc）
inspect.Parameter对象的default属性：如果这个参数有默认值，即返回这个默认值，如果没有，返回一个inspect._empty类。


对象已经正确的初始化了。
1.getmembers(object[, predicate])
返回一个包含对象的所有成员的(name, value)列表。返回的内容比对象的__dict__包含的内容多，源码是通过dir()实现的。
predicate是一个可选的函数参数，被此函数判断为True的成员才被返回。

2.getmodule(object)返回定义对象的模块

3.getsource(object)返回对象的源代码

4.getsourcelines(object)返回一个元组，元组第一项为对象源代码行的列表，第二项是第一行源代码的行号
ismodule,isclass,ismethod,isfunction,isbuiltin
一系列判断对象类型的方法，大都是包装了isinstance(object, types.FunctionType)之类语句的函数。

5.getargspec(func)
返回一个命名元组ArgSpect(args, varargs, keywords, defaults)，args是函数位置参数名列表，varargs是*参数名，
keywords是**参数名，defaults是默认参数值的元组。
在用__init__参数自动初始化实例属性的实践中，是用字节码对象的co_varnames属性来获取函数的位置参数名的
'''
# test
import inspect
def a(a, b=0, *c, d, e=1, **f):
    pass
aa = inspect.signature(a)
print("inspect.signature（fn)是:%s" % aa)
print("inspect.signature（fn)的类型：%s" % (type(aa)))
print("\n")

bb = aa.parameters
print("signature.paramerters属性是:%s" % bb)
print("ignature.paramerters属性的类型是%s" % type(bb))
print("\n")

for cc, dd in bb.items():
    print("mappingproxy.items()返回的两个值分别是：%s和%s" % (cc, dd))
    print("mappingproxy.items()返回的两个值的类型分别是：%s和%s" % (type(cc), type(dd)))
    print("\n")
    ee = dd.kind
    print("Parameter.kind属性是:%s" % ee)
    print("Parameter.kind属性的类型是:%s" % type(ee))
    print("\n")
    gg = dd.default
    print("Parameter.default的值是: %s" % gg)
    print("Parameter.default的属性是: %s" % type(gg))
    print("\n")


ff = inspect.Parameter.KEYWORD_ONLY
print("inspect.Parameter.KEYWORD_ONLY的值是:%s" % ff)
print("inspect.Parameter.KEYWORD_ONLY的类型是:%s" % type(ff))

