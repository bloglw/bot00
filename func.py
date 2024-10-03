import datetime
import uuid
import json
import requests
import sqlite3
import time
import telegram
from config import TOKEN, RATE, TRADE_DELETE_TIME, MASTER_WALLET_PRIVATE_KEY, TRONGRID_API_KEY
from tronpy import Tron
from tronpy.keys import PrivateKey

bot = telegram.Bot(token=TOKEN)

# Initialize Tron API
client = Tron(network='mainnet')

# 通过私钥生成地址并设置为默认地址
private_key_obj = PrivateKey(bytes.fromhex(MASTER_WALLET_PRIVATE_KEY))
tron = Tron()
tron.default_address = private_key_obj.public_key.to_base58check_address()


def get_random_num():
    return int('{0:%d%H%M%S%f}'.format(datetime.datetime.now()))


def get_uuid():
    return uuid.uuid1()


def generate_usdt_wallet():
    """
    Generate a new USDT wallet address and private key using the HD wallet mechanism.
    """
    try:
        account = client.generate_address()
        usdt_address = account['base58check_address']
        usdt_key = account['private_key']
        return usdt_address, usdt_key
    except Exception as e:
        print(f"Error generating USDT wallet: {e}")
        return None, None


def update_one_from_db(table_name, data_name, data_value, target_name, target_value):
    try:
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update {} set {}=? where {}=?".format(table_name, data_name, target_name),
                       (data_value, target_value,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)


def selectone_one_from_db(data_name, table_name, target, target_value):
    try:
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select {} from {} where {}=?".format(data_name, table_name, target), (target_value,))
        rst = cursor.fetchone()[0]
        conn.close()
        return rst
    except Exception as e:
        print(e)


def selectall_one_from_db(table_name, target, target_value):
    try:
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from {} where {}=?".format(table_name, target), (target_value,))
        rst = cursor.fetchone()
        conn.close()
        return rst
    except Exception as e:
        print(e)


def selectone_all_from_db(data_name, table_name, target, target_value):
    try:
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select {} from {} where {}=?".format(data_name, table_name, target), (target_value,))
        rst = cursor.fetchall()
        conn.close()
        rst_list = []
        for i in rst:
            rst_list.append(i[0])
        return rst_list
    except Exception as e:
        print(e)


def selectall_all_from_db(table_name, target, target_value):
    try:
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from {} where {}=?".format(table_name, target), (target_value,))
        rst = cursor.fetchall()
        conn.close()
        return rst
    except Exception as e:
        print(e)


def check_user_status(user_id):
    user_status = selectone_one_from_db('status', 'user', 'tg_id', user_id)
    if user_status == '开张' or user_status == '打烊':
        return True
    else:
        return False


def get_now_time():
    return int(time.time())


def struct_time(int_time):
    struct_time = time.localtime(int(int_time))
    year = struct_time.tm_year
    mon = struct_time.tm_mon
    day = struct_time.tm_mday
    hour = struct_time.tm_hour
    min = struct_time.tm_min
    sec = struct_time.tm_sec
    return '*{}-{}-{} {}:{}:{}*'.format(year, mon, day, hour, min, sec)


def delete_invoice():
    while True:
        try:
            now_time = get_now_time()
            conn = sqlite3.connect('data.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from invoice where type=? and status=?", ('充币', '待转账'))
            rst = cursor.fetchall()
            conn.close()
            if len(rst) > 0:
                for i in rst:
                    if int(i[2])+43200 < now_time:
                        invoice_id = i[0]
                        user_tgid = i[1]
                        try:
                            bot.send_message(
                                chat_id=user_tgid,
                                text='充值系统未监测到您的转账，地址自动作废，请勿往此地址发起转账！\n'
                                     '截止看到此信息，如果之前您已经转账却未到账，请联系客服！'
                            )
                        except:
                            print('用户可能已经禁用该bot，信息无法到达')
                        update_one_from_db('invoice', 'status', '未使用', 'uid', invoice_id)
            print('充值系统轮询完毕，休眠20s')
            time.sleep(20)
        except Exception as e:
            print(e)
            print('充值系统轮询错误，请检查！休眠20s')
            time.sleep(20)


def trade_monitor():
    while True:
        try:
            now_time = get_now_time()
            conn = sqlite3.connect('data.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from trade where trade_status=? and buyer_status=? and seller_status=?",
                           ('交易中', '待收货', '已发货',))
            rst = cursor.fetchall()
            conn.close()
            if len(rst) > 0:
                for i in rst:
                    trade_id, buyer_tgid, seller_tgid, end_time, usdt_amount = i[0], i[2], i[3], i[9], i[11]
                    if int(end_time) < int(now_time):
                        trade_comfirm(trade_id, buyer_tgid, seller_tgid, usdt_amount)
            conn = sqlite3.connect('data.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from trade where trade_status=? and buyer_status=? and seller_status=?",
                           ('交易中', '申请退款', '待发货',))
            rst = cursor.fetchall()
            conn.close()
            if len(rst) > 0:
                for i in rst:
                    trade_id, buyer_tgid, seller_tgid, end_time, usdt_amount = i[0], i[2], i[3], i[9], i[11]
                    if int(end_time) < int(now_time):
                        trade_cancel(trade_id, buyer_tgid, seller_tgid, usdt_amount)
            conn = sqlite3.connect('data.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from trade where trade_status=? and buyer_status=? and seller_status=?",
                           ('交易中', '申请退款', '已发货',))
            rst = cursor.fetchall()
            conn.close()
            if len(rst) > 0:
                for i in rst:
                    trade_id, buyer_tgid, seller_tgid, end_time, usdt_amount = i[0], i[2], i[3], i[9], i[11]
                    if int(end_time) < int(now_time):
                        trade_cancel(trade_id, buyer_tgid, seller_tgid, usdt_amount)
            conn = sqlite3.connect('data.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from trade where trade_status=? and buyer_status=? and seller_status=?",
                           ('交易中', '申请退款', '拒绝退款',))
            rst = cursor.fetchall()
            conn.close()
            if len(rst) > 0:
                for i in rst:
                    trade_id, buyer_tgid, seller_tgid, end_time, usdt_amount = i[0], i[2], i[3], i[9], i[11]
                    if int(end_time) < int(now_time):
                        trade_comfirm(trade_id, buyer_tgid, seller_tgid, usdt_amount)
            print('订单轮询完毕，休眠20s')
            time.sleep(20)
        except Exception as e:
            print(e)
            print('订单轮询错误，请检查！休眠60s')
            time.sleep(20)


def trade_comfirm(trade_id, buyer_tgid, seller_tgid, usdt_amount):
    try:
        update_one_from_db('trade', 'trade_status', '交易完成', 'uid', trade_id)
        update_one_from_db('trade', 'buyer_status', '已收货', 'uid', trade_id)
        seller_available_balance = int(selectone_one_from_db('available_balance', 'user', 'tg_id', seller_tgid))
        now_balance = int(seller_available_balance) + int((1-RATE)*float(usdt_amount))
        update_one_from_db('user', 'available_balance', int(now_balance), 'tg_id', seller_tgid)
        bot.send_message(
            chat_id=buyer_tgid,
            text='系统提示：您购买的商品超时未收货，系统已为您自动收货完成'
        )
        bot.send_message(
            chat_id=seller_tgid,
            text='系统提示：交易完成，由于买家超时未收货，系统已自动收货完成，款项已经到达您的账户，请查收！'
        )
    except Exception as e:
        print(e)


def trade_cancel(trade_id, buyer_tgid, seller_tgid, usdt_amount):
    try:
        update_one_from_db('trade', 'trade_status', '交易取消', 'uid', trade_id)
        update_one_from_db('trade', 'seller_status', '已退款', 'uid', trade_id)
        buyer_available_balance = int(selectone_one_from_db('available_balance', 'user', 'tg_id', buyer_tgid))
        now_balance = int(buyer_available_balance) + int(usdt_amount)
        update_one_from_db('user', 'available_balance', int(now_balance), 'tg_id', buyer_tgid)
        bot.send_message(
            chat_id=buyer_tgid,
            text='系统提示：由于卖家未及时处理您的退款申请，系统已自动为您取消订单，款项已经退回到您的账户，请查收！'
        )
        bot.send_message(
            chat_id=seller_tgid,
            text='系统提示：由于您未及时处理买家的退款申请，系统已自动取消订单，款项已经退回到买家的账户，如有异议请联系客服！'
        )
    except Exception as e:
        print(e)


def del_complete_trade():
    try:
        now_time = get_now_time()
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from trade where trade_status=?", ('交易完成',))
        complete_trades = cursor.fetchall()
        conn.close()
        if len(complete_trades) > 0:
            for i in complete_trades:
                trade_id, buyer_tgid, seller_tgid, end_time, usdt_amount = i[0], i[2], i[3], i[9], i[11]
                if int(end_time) + int(TRADE_DELETE_TIME*86400) < int(now_time):
                    conn = sqlite3.connect('data.sqlite3')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM trade WHERE uid=?", (trade_id,))
                    conn.commit()
                    conn.close()
        print('过期订单删除完成，休眠2分钟')
    except Exception as e:
        print(e)
        print('过期订单删除失败，请检查错误')
