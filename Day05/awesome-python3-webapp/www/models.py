# -*- coding: utf-8 -*-
"""
@author:Ding
@time:2018/5/23 14:17
"""

####三.编写Model（类似于javaweb中的domain对象信息）

##在编写ORM时，给一个Field增加一个default参数可以让ORM自己填入缺省值，非常方便。并且，缺省值可以作为函数对象传入，
##在调用save()时自动计算。
##例如，主键id的缺省值是函数next_id，创建时间created_at的缺省值是函数time.time，可以自动设置当前日期和时间。
##日期和时间用float类型存储在数据库中，而不是datetime类型，这么做的好处是不必关心数据库的时区以及时区转换问题，
##排序非常简单，显示的时候，只需要做一个float到str的转换，也非常容易。

import time,hashlib,uuid

from www.orm import Model,StringField,IntegerField,BooleanField,FloatField,TextField,select
from www.exception.exception import SQLException

def next_id():
    # md5 = hashlib.md5()
    # md5.upate('ding'.encode('utf-8'))
    # print(md5.hexdigest())

    #15位整数，不够前面补0
    #uuid.uuid4随机生成一个UUID(hex:转成十六进制)
    #Data too long for column
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    #id,username,password,admin,email,image,created_at(传入函数名即可)
    id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    username = StringField(ddl='varchar(40)')
    password = StringField(ddl='varchar(40)')
    admin = BooleanField()
    email = StringField(ddl='varchar(40)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)

    #复写父类的save方法，添加查重方法
    async def save(self):
        if(await self.isSaved()) == False:
            # return Model.save()
            await super(User,self).save()
        else:
            raise SQLException('该用户已经被注册！')

    #判断用户是否存在于数据库
    async def isSaved(self):
        sql = '%s where `%s`=?'%(self.__select__,'email')
        rs = await select(sql,[self.email])
        if len(rs) == 0:
            return False
        return True

class Blog(Model):
    __table__ = 'blogs'

    #id,user_id,user_name,user_image,name,summary,content,created_at
    id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(40)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(40)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()#默认是text类型
    created_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    #id,blog_id,user_id,user_name,user_image,content,created_at
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(40)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)