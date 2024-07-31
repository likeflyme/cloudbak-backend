import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.sys_db import SessionLocal
from app.dependencies.auth_dep import pwd_context
from app.models.sys import SysUser


def create():
    username = input("请输入用户名: ")
    print(f"您输入的用户名: {username}")

    password = input_pass()
    print(f"您输入的密码：{password}")

    session = SessionLocal()

    try:
        password = pwd_context.hash(password)
        user = SysUser(username=username, password=password, nickname=username, state=1)
        session.add(user)
        session.commit()
        print("用户添加成功")
    finally:
        session.close()


def input_pass():
    password = input("请输入密码: ")

    repeat_pass = input("请重复密码：")

    if password != repeat_pass:
        print("两次输入的密码不匹配")
        return input_pass()
    return password


try:
    create()
except KeyboardInterrupt as e:
    print('用户中断操作')
except Exception as e:
    print(e)
