# 1. ORM 概念

## 1.1 什么是 ORM

关系对象映射：

​	类			->	表

​	对象		->	记录（一行数据）

当有了对应关系滞后，不再需要编写 SQL 语句，取而代之的是操作：类、对象

### 1.1.1 概念

- db first：根据数据库的表生成类
- code first：根据类创建数据库表



# 2. 表关系

## 2.1  外键：建立表之间的关系

### 简介

「外键」就是用来帮助我们建立「表与表」之间的关系的：

```py
foreign key(字段名)
```

### foreign key 的创建

- 一对一关系：
- 一对多关系：foreign key 建在多的一方「表」
- 多对多关系

提示⚠️：

- 在建表的时候，一定要先创建「被关联」表
- 在录入数据的时候，也必须先录入「被关联」表

## 2.2 表之间的四种关系

数据库表之间的「四种」关系：

```she
- 一对一
- 一对多
- 多对多
- 没有关系
```

### 2.2.1 SQL 语句建表关系：一对一

#### 注意事项

- 「一对一」外键的创建：对于「一对一」关系表，`foreign key` 建在任意一方都可以，但是推荐建在「查询频率」比较高的表中
- 如果表关系是唯一的，需要加关键字：`unique`

#### 使用场景：

- 如果「用户详细信息」比较多，每次查看用户资料的时候，都会从数据库把所有信息「查询」、「展示」出来，这样造成了「数据库的压力」。

#### 案例：「用户表」和「用户详情表」

`分析 1`

​	将「用户表」拆分为：

- 「用户表」：ID、name、age
- 「用户详情表」：ID、addr、phone、hobby、email.....

```py
1）用户表角度
		一个用户能否对应多个用户详情：不能！！！

2）用户详情表角度
		一个详情能否属于多个用户：不能！！！
		
3）结论
		单向的一对多都不成立，那么多这个时候两者之间的表关系：一对一 或者就是没关系
```

`分析 2`

​	「客户表」和 「vip 客户表」

```py
1）客户表
		一个客户能否多个 vip客户信息？		不能！！！

2）vip 客户表
		一个vip 客户是否对应多个客户？		不能！！！
   
3）结论
		a. 在充值 vip 之前，都是普通客户
		b. 充值 vip 之后，vip 客户表就会记录充值 vip 的普通用户信息
```



`作者详情表`：先创建

```pyt
create table authordetail(
		id int primary key auto_increment,
		phone int,
		addr varchar(64),
);
```

`作者表`

```py
create table author(
		id int primary key auto_increment,
		name varchar(64),
		age int,
		authordetail_id int unique,		# 如果「一对一」表关系是唯一的，需要加 `unique` 关键子
		foreign key(authordetail_id) references authordetail(id)
		on update cascade
		on delete cascade
);
```



### 2.2.2 SQL 语句建表关系：一对多

`分析`

判断表之间关系的时候，前期不熟悉的情况下，一定要「**换位思考**」，分别站在两张表的角度考虑。

```pytho
案例：员工表与部门表为例：
	1）员工表角度
		思考「一个员工」能否对应多个部门（一个员工数据能否对应多条部门数据）？
		答案：不能！！！（不能直接得出结论，一定要两张表都考虑完全）
	2）部门表角度
		思考「一个部门」能否对应多个员工（一个部门数据能否对应多条员工数据）？
		答案：能！！！
	
	3）得出结论
		「员工表」与「部门表」表示单向一对多
		
```

#### 注意事项：



#### 案例：「员工表」和「部门表」

`部门表`

```py
create table dep(
		id int primary key, auto_increment,
		dep_name	char(16),
		dep_desc	char(32)
);
```

`员工表`

```py
create table emp(
		id int primary key, auto_increment,
		emp_name		char(16),
		emp_gender	enum('male', 'famale', 'others') default 'male',
		dep_id int,
		foreign key(dep_id) references dep(id)	# 声明外键字段，和哪张表有关系
);
```

#### 修改表里面的字段：更改、删除

- 单独的修改、删除存在有表关系的数据是「不行」的

真正做到数据之间有关系：

- 更新就同步更新：级联更新
- 删除就同步删除：级联删除

`方法：案例`

```py
foreign key(dep_id) references dep(id) 
on update cascade		# 同步更新
on delete cascade		# 同步删除
```



### 2.2.3 SQL 语句建立表关系：多对多

#### 注意事项：

- 针对「多对多」字段表关系，不能在来个两张原有表中创建「foreign key」，需要单独创建一张表存储：`两张表之间的关系`

#### 案例：「书籍表」和「作者表」

`分析`

```py
1）书籍表角度
		一本书可不可以有多个作者？		可以！！！
2）作者角度
		一个作者可不可以有多本书？		可以！！！
		
3）结论
		「书籍表」和「作者表」是：双向一对多关系，那么表关系就是「多对多」关系
```

`关系映射表`

```py
create table book2author(
		id int primary key auto_increment,
		book_id int,
		author_id int;
		foreign key(book_id) references book(id)
		on update cascade
		on delete cascade,
		foreign key(author_id) references author(id)
		on update cascade
		on delete cascade
);
```

`书籍表` 

```py
create table book(
		id int primary key auto_increment,
		title	varchar(32),
		price	float,
		author_id	int,
		
);
```

`作者表`

```pyt
create table author(
		id int primary key auto_increment,
		name varchar(32),
		age	int,
		book_id int,
		
);
```

