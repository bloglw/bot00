import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN
import sqlite3
from config import ADMIN_ID, BOT_USERNAME, RATE
from func import selectall_one_from_db, struct_time, update_one_from_db, get_now_time
from func import selectone_one_from_db, selectone_all_from_db

ROUTE, FUNC_EXEC, TRADE_ROUTE, MESSAGE_ROUTE = range(4)
bot = telegram.Bot(token=TOKEN)


def admin_start(update, context):
    if is_admin(update, context):
        keyboard = [
            [InlineKeyboardButton("查询用户信息", callback_data=str('查询用户信息')),
             InlineKeyboardButton("查看所有交易", callback_data=str('查看所有交易'))],
            [InlineKeyboardButton("更改钱包状态", callback_data=str('更改用户状态')),
             InlineKeyboardButton("更改用户余额", callback_data=str('更改用户余额'))],
            [InlineKeyboardButton("更改店铺状态", callback_data=str('更改店铺状态')),
             InlineKeyboardButton("更改商品状态", callback_data=str('更改商品状态'))],
            [InlineKeyboardButton("更改订单状态", callback_data=str('更改订单状态')),
             InlineKeyboardButton("推送消息", callback_data=str('推送消息'))],
        ]
        update.message.reply_text(
            '请选择您要进行的操作：',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ROUTE


def get_user_input(update, context):
    try:
        query = update.callback_query
        query.answer()
        # user_id = update.effective_user.id
        choose_fun = query.data
        context.user_data['func'] = choose_fun
        if choose_fun == '查询用户信息' or choose_fun == '更改用户状态' or choose_fun == '更改用户余额' or choose_fun == '更改店铺状态':
            query.edit_message_text(
                text="请输入用户的Telegram ID 或者 商城的 UUID",
            )
            return ROUTE
        elif choose_fun == '更改商品状态':
            query.edit_message_text(
                text="请输入商品ID，商品访问链接后面的数字即为商品ID",
            )
            return ROUTE
        elif choose_fun == '更改订单状态':
            query.edit_message_text(
                text="请输入订单ID，订单访问链接后面的数字即为订单ID",
            )
            return ROUTE
    except Exception as e:
        print(e)


def choose_func(update, context):
    print('进入 choose_func 函数')
    user_id = update.effective_user.id
    user_input = update.message.text
    print(user_input)
    choose_fun = context.user_data['func']
    context.user_data['user_input'] = user_input
    if choose_fun == '查询用户信息' or choose_fun == '更改用户状态' or choose_fun == '更改用户余额' or choose_fun == '更改店铺状态':
        rst = user_info(user_input)
        if rst is None:
            bot.send_message(
                chat_id=user_id,
                text='该用户不存在数据库中，请重新输入，退出 /icancel'
            )
            return ROUTE
        query_tgid, query_uuid, query_available_balance, query_shop_status, query_shop_address, query_wallet_status = \
            rst[0], rst[1], rst[3], rst[4], rst[5], rst[9]  # 调整了数据库字段索引
        context.user_data['query_tgid'] = query_tgid
        ret_text = '查询成功，该用户信息如下：\n' \
                   'TG ID：`{}`\n' \
                   'UUID：`{}`\n' \
                   '可用余额：{} USDT\n' \
                   '店铺状态：{}\n' \
                   '店铺地址：[点击访问](https://t.me/{}?start=shop{})\n' \
                   '钱包状态：{}\n'.format(query_tgid, query_uuid, query_available_balance, query_shop_status,
                                      BOT_USERNAME, query_shop_address, query_wallet_status)
        if choose_fun == '查询用户信息':
            print('查询用户信息')
            update.message.reply_text(
                ret_text,
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        elif choose_fun == '更改用户状态':
            print('更改用户状态')
            keyboard = [
                [InlineKeyboardButton("锁定钱包", callback_data=str('锁定钱包')),
                 InlineKeyboardButton("解锁钱包", callback_data=str('解锁钱包'))]
            ]
            update.message.reply_text(
                ret_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return FUNC_EXEC
        elif choose_fun == '更改用户余额':
            print('更改用户余额')
            context.user_data['query_uuid'] = query_uuid
            keyboard = [
                [InlineKeyboardButton("增加余额", callback_data=str('增加余额')),
                 InlineKeyboardButton("减少余额", callback_data=str('减少余额'))]
            ]
            update.message.reply_text(
                ret_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return FUNC_EXEC
        elif choose_fun == '更改店铺状态':
            print('更改店铺状态')
            keyboard = [
                [InlineKeyboardButton("锁定店铺", callback_data=str('锁定店铺')),
                 InlineKeyboardButton("解锁店铺", callback_data=str('解锁店铺'))]
            ]
            update.message.reply_text(
                ret_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return FUNC_EXEC


def user_info(user_id):
    try:
        print('进入 user_info 函数')
        rst = selectall_one_from_db('user', 'tg_id', user_id)
        # print(rst)
        if rst is None:
            rst = selectall_one_from_db('user', 'uuid', user_id)
            # print(rst)
        return rst
    except Exception as e:
        print(e)


def admin_cancel(update, context):
    pass


def is_admin(update, context):
    if update.message.from_user.id in ADMIN_ID:
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='*非管理员，无权操作*',
            parse_mode='Markdown'
        )
        return False


def func_exec(update, context):
    try:
        admin_id = update.effective_user.id
        print('进入 func_exec 函数')
        query = update.callback_query
        query.answer()
        # user_id = update.effective_user.id
        choose_func_exec = query.data
        choose_func = context.user_data['func']
        user_input = context.user_data['user_input']
        context.user_data['choose_func_exec'] = choose_func_exec
        print(choose_func, user_input, choose_func_exec)
        if choose_func == '更改用户状态':
            if choose_func_exec == '锁定钱包':
                query_tgid = context.user_data['query_tgid']
                print(query_tgid)
                update_one_from_db('user', 'wallet_status', '锁定', 'tg_id', query_tgid)
                bot.send_message(
                    chat_id=admin_id,
                    text='钱包已锁定'
                )
            elif choose_func_exec == '解锁钱包':
                query_tgid = context.user_data['query_tgid']
                print(query_tgid)
                update_one_from_db('user', 'wallet_status', '激活', 'tg_id', query_tgid)
                bot.send_message(
                    chat_id=admin_id,
                    text='钱包已解锁'
                )
        elif choose_func == '更改用户余额':
            if choose_func_exec == '增加余额':
                query.edit_message_text(
                    text='请回复需要增加的数目(单位USDT)：',
                )
                return FUNC_EXEC
            elif choose_func_exec == '减少余额':
                query.edit_message_text(
                    text='请回复需要减少的数目(单位USDT)：',
                )
                return FUNC_EXEC
        elif choose_func == '更改店铺状态':
            if choose_func_exec == '锁定店铺':
                query_tgid = context.user_data['query_tgid']
                print(query_tgid)
                update_one_from_db('user', 'status', '锁定', 'tg_id', query_tgid)
                bot.send_message(
                    chat_id=admin_id,
                    text='店铺已锁定'
                )
            elif choose_func_exec == '解锁店铺':
                query_tgid = context.user_data['query_tgid']
                print(query_tgid)
                update_one_from_db('user', 'status', '开张', 'tg_id', query_tgid)
                bot.send_message(
                    chat_id=admin_id,
                    text='店铺已解锁'
                )
        elif choose_func == '更改商品状态':
            if choose_func_exec == '管理锁定':
                print(user_input)
                update_one_from_db('goods', 'status', '锁定', 'uid', user_input)
                bot.send_message(
                    chat_id=admin_id,
                    text='商品已锁定'
                )
            elif choose_func_exec == '管理解锁':
                print(user_input)
                update_one_from_db('goods', 'status', '上架', 'uid', user_input)
                bot.send_message(
                    chat_id=admin_id,
                    text='商品已解锁'
                )
        elif choose_func == '更改订单状态':
            if choose_func_exec == '管理确认收货':
                now_time = get_now_time()
                update_one_from_db('trade', 'buyer_status', '已收货', 'uid', user_input)
                update_one_from_db('trade', 'seller_status', '已发货', 'uid', user_input)
                update_one_from_db('trade', 'trade_status', '交易完成', 'uid', user_input)
                update_one_from_db('trade', 'end_time', now_time, 'uid', user_input)
                buyer_tgid = selectone_one_from_db('buyer_tgid', 'trade', 'uid', user_input)
                seller_tgid = selectone_one_from_db('seller_tgid', 'trade', 'uid', user_input)
                price = selectone_one_from_db('price', 'trade', 'uid', user_input)
                seller_balance = selectone_one_from_db('balance', 'user', 'tg_id', seller_tgid)
                now_balance = float(seller_balance) + round((1 - RATE) * float(price), 2)
                update_one_from_db('user', 'balance', now_balance, 'tg_id', seller_tgid)
                bot.send_message(
                    chat_id=admin_id,
                    text='订单已收货'
                )
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='管理员裁决：交易完成，您已确认收货，款项已经打至卖家账户！'
                )
                bot.send_message(
                    chat_id=seller_tgid,
                    text='管理员裁决：交易完成，买家确认收货，款项已经打至您账户，请查收！'
                )
            elif choose_func_exec == '管理确认退款':
                now_time = get_now_time()
                update_one_from_db('trade', 'buyer_status', '申请退款', 'uid', user_input)
                update_one_from_db('trade', 'seller_status', '已退款', 'uid', user_input)
                update_one_from_db('trade', 'trade_status', '交易取消', 'uid', user_input)
                update_one_from_db('trade', 'end_time', now_time, 'uid', user_input)
                buyer_tgid = selectone_one_from_db('buyer_tgid', 'trade', 'uid', user_input)
                seller_tgid = selectone_one_from_db('seller_tgid', 'trade', 'uid', user_input)
                price = selectone_one_from_db('price', 'trade', 'uid', user_input)
                buyer_balance = selectone_one_from_db('balance', 'user', 'tg_id', buyer_tgid)
                now_balance = float(buyer_balance) + float(price)
                update_one_from_db('user', 'balance', now_balance, 'tg_id', buyer_tgid)
                bot.send_message(
                    chat_id=admin_id,
                    text='订单已退款'
                )
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='管理员裁决：交易取消，退款成功，款项已经退回至您的账户，请查收！'
                )
                bot.send_message(
                    chat_id=seller_tgid,
                    text='管理员裁决：交易取消，订单已退款，款项已经退回买家账户！'
                )
    except Exception as e:
        print(e)


def balance_exec(update, context):
    try:
        print('进入 balance_exec 函数')
        change_usdt_amount = float(update.message.text)
        query_uuid = context.user_data['query_uuid']
        choose_func_exec = context.user_data['choose_func_exec']
        print(change_usdt_amount, query_uuid)
        user_balance = float(selectone_one_from_db('available_balance', 'user', 'uuid', query_uuid))  # 改为 float 类型
        print(user_balance)
        if choose_func_exec == '增加余额':
            now_balance = user_balance + change_usdt_amount
            update_one_from_db('user', 'available_balance', now_balance, 'uuid', query_uuid)
            try:
                bot.send_message(
                    chat_id=query_uuid,
                    text='您的账户当前到账：{} USDT'.format(change_usdt_amount)
                )
            except Exception as e:
                print(e)
            update.message.reply_text('用户余额增加完毕')
        elif choose_func_exec == '减少余额':
            if user_balance - change_usdt_amount < 0:
                update.message.reply_text('用户当前余额不足，不足以减少对应的 USDT 数量')
            else:
                now_balance = user_balance - change_usdt_amount
                update_one_from_db('user', 'available_balance', now_balance, 'uuid', query_uuid)
                try:
                    bot.send_message(
                        chat_id=query_uuid,
                        text='您的账户余额减少：{} USDT'.format(change_usdt_amount)
                    )
                except Exception as e:
                    print(e)
                update.message.reply_text('用户余额减少完毕')
        print('增加完毕')

    except Exception as e:
        print(e)



def invoice_entry(update, context):
    try:
        print('进入 invoice_entry 函数')
        query = update.callback_query
        query.answer()
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select creat_time from trade")
        rst = cursor.fetchall()
        creat_time_list = []
        if len(rst) > 0:
            for i in rst:
                creat_time_list.append(int(i[0]))
        cursor.execute("select creat_time from invoice where status!='待转账' and status!='未使用'")
        rst = cursor.fetchall()
        conn.close()
        if len(rst) > 0:
            for i in rst:
                creat_time_list.append(int(i[0]))
        creat_time_list.sort(reverse=True)
        print(creat_time_list)
        if len(creat_time_list) > 30:
            creat_time_list = creat_time_list[:30]
        ret_text = ''
        for j in creat_time_list:
            trade_info = selectall_one_from_db('trade', 'creat_time', j)
            if trade_info is None:
                invoice_info = selectall_one_from_db('invoice', 'creat_time', str(j))
                invoice_uid, user_tgid, creat_time, invoice_type, invoice_address, usdt_amount = \
                    invoice_info[0], invoice_info[1], invoice_info[2], invoice_info[3], invoice_info[6], invoice_info[4]
                if usdt_amount is None:
                    usdt_amount = 0
                if invoice_type == '充币':
                    ret_text += "[{}](tg://user?id={}) 充币 *{}* USDT {}\n".format(
                        user_tgid, user_tgid, usdt_amount, struct_time(creat_time))
                elif invoice_type == '提币':
                    ret_text += "[{}](tg://user?id={}) 提币 *{}* USDT {}\n".format(
                        user_tgid, user_tgid, usdt_amount, struct_time(creat_time))
                elif invoice_type == '转账':
                    ret_text += "[{}](tg://user?id={}) 向 [{}](tg://user?id={}) 转账 *{}* USDT {}\n".format(
                        user_tgid, user_tgid, invoice_address, invoice_address, usdt_amount, struct_time(creat_time))
            else:
                trade_uid, goods_uid, buyer_tgid, seller_tgid, goods_price, creat_time = \
                    trade_info[0], trade_info[1], trade_info[2], trade_info[3], trade_info[4], trade_info[8]
                goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
                ret_text += "[{}](tg://user?id={}) 向 [{}](tg://user?id={}) 购买 [{}](https://t.me/{}?start=goods{})，*{}* USDT，{}\n".format(
                    buyer_tgid, buyer_tgid, seller_tgid, seller_tgid, goods_name, BOT_USERNAME, goods_uid, goods_price,
                    struct_time(creat_time)
                )
        keyboard = [
            [InlineKeyboardButton("充币", callback_data=str('充币')),
             InlineKeyboardButton("提币", callback_data=str('提币'))],
            [InlineKeyboardButton("转账", callback_data=str('转账')),
             InlineKeyboardButton("买卖", callback_data=str('买卖'))],
        ]
        query.edit_message_text(
            text=ret_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return TRADE_ROUTE
    except Exception as e:
        print(e)


def invoice_func(update, context):
    try:
        print('进入 invoice_func 函数')
        query = update.callback_query
        query.answer()
        choose_type = query.data
        print(choose_type)
        keyboard = [
            [InlineKeyboardButton("充币", callback_data=str('充币')),
             InlineKeyboardButton("提币", callback_data.str('提币'))],
            [InlineKeyboardButton("转账", callback_data.str('转账')),
             InlineKeyboardButton("买卖", callback_data.str('买卖'))],
        ]
        creat_time_list = []
        ret_text = ''
        now_time = get_now_time()
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        if choose_type == '充币':
            cursor.execute("select creat_time from invoice where status=?", ('已到账',))
            rst = cursor.fetchall()
            if len(rst) > 0:
                for i in rst:
                    if int(int(i[0]) + 86400*15) >= now_time:
                        creat_time_list.append(int(i[0]))
            creat_time_list.sort(reverse=True)
            for j in creat_time_list:
                invoice_info = selectall_one_from_db('invoice', 'creat_time', str(j))
                invoice_uid, user_tgid, creat_time, invoice_type, invoice_address, usdt_amount = \
                    invoice_info[0], invoice_info[1], invoice_info[2], invoice_info[3], invoice_info[6], invoice_info[4]
                ret_text += "[{}](tg://user?id={}) 充币 *{}* USDT {}\n".format(
                    user_tgid, user_tgid, usdt_amount, struct_time(creat_time))
        elif choose_type == '提币':
            cursor.execute("select creat_time from invoice where type=?", ('提币',))
            rst = cursor.fetchall()
            if len(rst) > 0:
                for i in rst:
                    if int(int(i[0]) + 86400*15) >= now_time:
                        creat_time_list.append(int(i[0]))
            creat_time_list.sort(reverse=True)
            for j in creat_time_list:
                invoice_info = selectall_one_from_db('invoice', 'creat_time', str(j))
                invoice_uid, user_tgid, creat_time, invoice_type, invoice_address, usdt_amount = \
                    invoice_info[0], invoice_info[1], invoice_info[2], invoice_info[3], invoice_info[6], invoice_info[4]
                ret_text += "[{}](tg://user?id={}) 提币 *{}* USDT {}\n".format(
                    user_tgid, user_tgid, usdt_amount, struct_time(creat_time))
        elif choose_type == '转账':
            cursor.execute("select creat_time from invoice where type=?", ('转账',))
            rst = cursor.fetchall()
            if len(rst) > 0:
                for i in rst:
                    if int(int(i[0]) + 86400*15) >= now_time:
                        creat_time_list.append(int(i[0]))
            creat_time_list.sort(reverse=True)
            for j in creat_time_list:
                invoice_info = selectall_one_from_db('invoice', 'creat_time', str(j))
                invoice_uid, user_tgid, creat_time, invoice_type, invoice_address, usdt_amount = \
                    invoice_info[0], invoice_info[1], invoice_info[2], invoice_info[3], invoice_info[6], invoice_info[4]
                ret_text += "[{}](tg://user?id={}) 向 [{}](tg://user?id={}) 转账 *{}* USDT {}\n".format(
                    user_tgid, user_tgid, invoice_address, invoice_address, usdt_amount, struct_time(creat_time))
        elif choose_type == '买卖':
            cursor.execute("select creat_time from trade")
            rst = cursor.fetchall()
            if len(rst) > 0:
                for i in rst:
                    if int(int(i[0]) + 86400*15) >= now_time:
                        creat_time_list.append(int(i[0]))
            creat_time_list.sort(reverse=True)
            for j in creat_time_list:
                trade_info = selectall_one_from_db('trade', 'creat_time', j)
                trade_uid, goods_uid, buyer_tgid, seller_tgid, goods_price, creat_time = \
                    trade_info[0], trade_info[1], trade_info[2], trade_info[3], trade_info[4], trade_info[8]
                goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
                ret_text += "[{}](tg://user?id={}) 向 [{}](tg://user?id={}) 购买 [{}](https://t.me/{}?start=goods{})，*{}* USDT，{}\n".format(
                    buyer_tgid, buyer_tgid, seller_tgid, seller_tgid, goods_name, BOT_USERNAME, goods_uid, goods_price,
                    struct_time(creat_time)
                )
        conn.close()
        query.edit_message_text(
            text=ret_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return TRADE_ROUTE
    except Exception as e:
        print(e)


def message_entry(update, context):
    try:
        print('进入 message_entry 函数')
        query = update.callback_query
        query.answer()
        choose_type = query.data
        query.edit_message_text(
            text='请回复需要群体发送的信息：',
        )
        return MESSAGE_ROUTE
    except Exception as e:
        print(e)


def escape_telegrambot_underscore(message):
        return message.replace("_", "\\_")


def message_exec(update, context):
    try:
        print('进入 message_exec 函数')
        message = escape_telegrambot_underscore(update.message.text)
        print(message)
        for i in ADMIN_ID:
            bot.send_message(
                chat_id=i,
                text="您将要发送的信息为：\n" + message + "\n信息将在后台陆续发送，发送完毕将会通知您",
                parse_mode='Markdown'
            )
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select tg_id from user")
        rst = cursor.fetchall()
        conn.close()
        user_list = []
        for i in rst:
            user_list.append(i[0])
        print(user_list)
        for user in user_list:
            try:
                bot.send_message(
                    chat_id=user,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(e)
                # continue
        for i in ADMIN_ID:
            bot.send_message(
                chat_id=i,
                text="消息群发完毕！",
                parse_mode='Markdown'
            )
    except Exception as e:
        print(e)


admin_handler = ConversationHandler(
    entry_points=[CommandHandler('iadmin', admin_start)],
    states={
        ROUTE: [
            CommandHandler('iadmin', admin_start),
            CallbackQueryHandler(get_user_input, pattern='^' + str('查询用户信息') + '$'),
            CallbackQueryHandler(get_user_input, pattern='^' + str('更改用户状态') + '$'),
            CallbackQueryHandler(get_user_input, pattern='^' + str('更改用户余额') + '$'),
            CallbackQueryHandler(get_user_input, pattern='^' + str('更改店铺状态') + '$'),
            CallbackQueryHandler(get_user_input, pattern='^' + str('更改商品状态') + '$'),
            CallbackQueryHandler(get_user_input, pattern='^' + str('更改订单状态') + '$'),
            CallbackQueryHandler(invoice_entry, pattern='^' + str('查看所有交易') + '$'),
            CallbackQueryHandler(message_entry, pattern='^' + str('推送消息') + '$'),
            MessageHandler(Filters.regex(r"\d+"), choose_func)
        ],
        FUNC_EXEC: [
            CommandHandler('iadmin', admin_start),
            CallbackQueryHandler(func_exec, pattern=
            '^' + '(锁定钱包|解锁钱包|增加余额|减少余额|锁定店铺|解锁店铺|管理锁定|管理解锁|管理确认收货|管理确认退款)' + '$'),
            MessageHandler(Filters.regex(r".*"), balance_exec)
        ],
        TRADE_ROUTE: [
            CommandHandler('iadmin', admin_start),
            CallbackQueryHandler(invoice_func, pattern='^' + str('充币') + '$'),
            CallbackQueryHandler(invoice_func, pattern='^' + str('提币') + '$'),
            CallbackQueryHandler(invoice_func, pattern='^' + str('转账') + '$'),
            CallbackQueryHandler(invoice_func, pattern='^' + str('买卖') + '$'),
        ],
        MESSAGE_ROUTE: [
            CommandHandler('iadmin', admin_start),
            MessageHandler(Filters.regex(r".*"), message_exec)
        ]
    },
    conversation_timeout=600,
    fallbacks=[CommandHandler('icancel', admin_cancel)]
)
