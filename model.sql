create database seat charset utf8;
DROP TABLE IF EXISTS optioninfo;
DROP TABLE if EXISTS userinfo;
DROP TABLE if EXISTS seatinfo;

CREATE TABLE IF NOT EXISTS userinfo(
	number CHAR(10) COMMENT '学号',
	name CHAR(10) COMMENT '姓名',
	PRIMARY KEY (number, name),
	email CHAR(20) COMMENT '电子邮件',
	t_m ENUM('times', 'monthly') DEFAULT 'times' COMMENT '是否包月',
	times INT DEFAULT 3 COMMENT '预约次数',
	start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '用户入户时间',
	end_date DATE COMMENT '包月结束时间',
	money INT DEFAULT 0 COMMENT '预交金额',
	whether INT DEFAULT 0 COMMENT '是否预约',
	password char(20) COMMENT '密码'
	)ENGINE=INNODB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS optioninfo(
	id INT PriMARY KEY auto_increment,
	number CHAR(10) NOT NULL COMMENT '学号',
	name CHAR(10) NOT NULL COMMENT '姓名',
	dates DATE COMMENT '开始定座日期',
	mutiple INT DEFAULT 0 COMMENT '是否预约多个时间段——》是否倒序预约',
	floor CHAR(10) COMMENT '楼层',
	seat1 CHAR(10) COMMENT '预选座位1',
	seat2 CHAR(10) COMMENT '预选座位2',
	seat3 CHAR(10) COMMENT '预选座位3',
	start1 CHAR(6) DEFAULT '08:00' COMMENT '预约开始时间',
	end1 CHAR(6) DEFAULT '22:00' COMMENT '预约结束时间',
	start2 CHAR(6) COMMENT '预约开始时间',
	end2 CHAR(6) COMMENT '预约结束时间',
	start3 CHAR(6) COMMENT '周三预约开始时间',
	end3 CHAR(6) COMMENT '周三预约结束时间',
	start4 CHAR(6) COMMENT '周三预约开始时间',
	end4 CHAR(6) COMMENT '周三预约结束时间',
	remark CHAR(64) COMMIT '备注',
	CONSTRAINT fk_user_name FOREIGN KEY (number,name) REFERENCES userinfo(number,name)
	ON UPDATE CASCADE
	ON DELETE CASCADE
	)ENGINE=INNODB DEFAULT CHARSET=utf8;


CREATE TABLE IF NOT EXISTS seatinfo(
	seat_name CHAR(10) PRIMARY KEY COMMENT '座位号',
	kindName CHAR(10) COMMENT '楼层',
	devId CHAR(10),
	labId CHAR(10),
	kindId CHAR(10),
	roomId char(10)
	)ENGINE=INNODB DEFAULT CHARSET=utf8;

alter table ipurl add column client_id char(35);
alter table ipurl add column client_secret char(35);

CREATE TABLE IF NOT EXISTS ipurl(
	url varchar(255) comment 'ip获取url',
	value char(100) comment 'token值',
	expire char(64) comment 'token过期时间',
	client_id char(35),
	client_secret char(35)
	)ENGINE=INNODB DEFAULT CHARSET=utf8;

# 支付日期
CREATE TABLE IF NOT EXISTS pay(
	id INT PriMARY KEY auto_increment,
	number CHAR(10) NOT NULL COMMENT '学号',
	name CHAR(10) NOT NULL COMMENT '姓名',
	money INT COMMENT '金额',
	pay_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '交钱时间',
	end_date DATE COMMENT '到期时间',
	CONSTRAINT fk_name FOREIGN KEY (number,name) REFERENCES userinfo(number,name)
	)ENGINE=INNODB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS accomplish(
	id INT PRIMARY KEY auto_increment,
	number CHAR(10) NOT NULL COMMENT '学号',
	name CHAR(10) NOT NULL COMMENT '姓名',
	date CHAR(15),
	suss1 INT DEFAULT 0 COMMENT '第一个时间段是否成功预约',
	suss2 INT DEFAULT 0 COMMENT '第二个时间段是否预约成功',
	CONSTRAINT fk_accomplish_name FOREIGN KEY (number,name) REFERENCES userinfo(number,name)
	)ENGINE=INNODB DEFAULT CHARSET=utf8;



CREATE TABLE IF NOT EXISTS recordmsg(
	number CHAR(10) NOT NULL COMMENT '学号',
	name CHAR(10) NOT NULL COMMENT '姓名',
	date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '时间',
	update_date datetime DEFAULT CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
	cookie TEXT COMMENT 'cookie',
	code CHAR(32) COMMENT '验证码',
	CONSTRAINT fk_recordmsg_name FOREIGN KEY (number,name) REFERENCES userinfo(number,name)
	)ENGINE=INNODB DEFAULT CHARSET=utf8;




































