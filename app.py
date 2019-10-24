import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web


# __pool 连接池, 连接池使用全局变量 __pool存储
async def cteate_pool(loop, **kw):
    logging.info('Create database connection pool....')
    # 设置全局变量
    global __pool
    # yield 配合 async 产生一个异步生成器
    # yield from 以委托控制流给一个子迭代器
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

# select 语句, 要执行SELECT语句，我们用select函数执行，需要传入SQL语句和SQL参数：
# SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。
# 注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。
# 注意到yield from将调用一个子协程（也就是在一个协程中调用另一个协程）并直接获得子协程的返回结果。
# 如果传入size参数，就通过fetchmany()获取最多指定数量的记录，否则，通过fetchall()获取所有记录。
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replance('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows returned:%s' % len(rs))
        return rs

# insert/updata/delete
# execute()函数和select()函数所不同的是，cursor对象不返回结果集，而是通过rowcount返回结果数
async def execute(sql, args):
    log(sql)
    with (yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replance('?', '%s'), args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        finally:
            return affected



# 协程函数, 可以有多个
# 必须是协程, 接收一个request, 返回一个response实例
# 也可以使用装饰器, @routes.get('/)
async def index(request):
    return web.Response(body=b'<h1>Awesome1</h1>', content_type='text/html')

# 管理协程的主函数, 入口, 这里需要速度特别快, 不要有cpu密集工作
async def init(loop):
    # 创建一个application实例
    app = web.Application(loop=loop)
    # 设置请求方法路径和处理请求程序
    app.router.add_route('GET', "/", index)
    # server是异步上下文管理器
    # await所在语句异步推导式。 异步推导式可以暂停执行它所在的协程函数
    # make_handler创建用于处理请求的http协议工厂
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000')
    return srv

if __name__ == "__main__":
    # 获取当前事件循环, 如果当前没有事件循环, 则创建一个事件循环
    loop = asyncio.get_event_loop()
    # 运行直到future实例被完成, 如果参数是协程, 则隐式调度asyncio.Task运行
    loop.run_until_complete(init(loop))
    # 运行循环事件直到调用stop()
    # 这里没有stop()语句, 就会一直运行下去
    loop.run_forever()