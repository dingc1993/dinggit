drop database if exists awesome;

create database awesome;

use awesome;

grant select, update, insert, delete on awesome.* to 'root'@'localhost' identified by 'root';

#id,username,password,admin,email,image,created_at
#engine innodb
#存储引擎是innodb。nnoDB 是 MySQL 上第一个提供外键约束的数据存储引擎，除了提供事务处理外，InnoDB 还支持行锁，
#提供和 Oracle 一样的一致性的不加锁读取，能增加并发读的用户数量并提高性能，不会增加锁的数量。InnoDB 的设计目标
#是处理大容量数据时最大化性能，它的 CPU 利用率是其他所有基于磁盘的关系数据库引擎中最有效率的。
create table users(
  `id` varchar(50) not null,
  `username` varchar(40) not null,
  `password` varchar(40) not null,
  `admin` bool not null,
  `email` varchar(40) not null,
  `image` varchar(500) not null,
  `created_at` real not null,
  unique key `idx_email` (`email`),
  key `idx_created_at` (`created_at`),
  primary key (`id`)
) engine=innodb default charset=utf8;

#id,user_id,user_name,user_image,name,summary,content,created_at
create table blogs(
  `id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(40) not null,
  `user_image` varchar(500) not null,
  `name` varchar(40) not null,
  `summary` varchar(200) not null,
  `content` mediumtext not null,
  `created_at` real not null,
  key `idx_created_at` (`created_at`),
  primary key (`id`)
) engine=innodb default charset=utf8;

#id,blog_id,user_id,user_name,user_image,content,created_at
create table comments(
  `id` varchar(50) not null,
  `blog_id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(40) not null,
  `user_image` varchar(500) not null,
  `content` varchar(500) not null,
  `created_at` real not null,
  key `idx_created_at` (`created_at`),
  primary key (`id`)
) engine=innodb default charset=utf8;