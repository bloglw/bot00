import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from config import TOKEN, BOT_USERNAME
from func import selectone_one_from_db, selectall_one_from_db
from func import get_now_time, struct_time, update_one_from_db
import re

bot = telegram.Bot(token=TOKEN)


def trade_display(update, context):
    try:
        user_id = update.effective_user.id
        print('进入 trade_display 函数 | ' + str(user_id))
        text = update.message.text
        rst = re.search(r"/start\s(goods|shop|trade)(\d+)", text)
        trade_uid = rst.group(2)
        print(trade_uid)
        context.user_data['trade_uid'] = trade_uid
        trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
        goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
            trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
        seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
            trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
        goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
        if user_id == seller_tgid:
            if trade_status == '交易中':
                if buyer_status == '申请退款' and seller_status != '拒绝退款':
                    keyboard = [
                        [InlineKeyboardButton("同意退款", callback_data=str('同意退款')),
                         InlineKeyboardButton("拒绝退款", callback_data=str('拒绝退款'))],
                    ]
                    bot.send_message(
                        chat_id=user_id,
                        text='该订单买家已经申请退款，如果您不响应买家的退款申请，交易会在2天后自动退款\n'
                             '💎商品名：[{}](https://t.me/{}?start=goods{})\n'
                             '💎订单创建时间：{}\n'
                             '🔴结束时间：{}\n'
                             '💎价格：*{}* USDT\n'
                             '🔴状态：{}\n'
                             '🔴详细状态：{}\n'
                             '💎[联系买家](tg://user?id={}) (无法点击说明已销号)'.format
                        (goods_name, BOT_USERNAME, goods_uid, struct_time(creat_time),
                         struct_time(end_time), usdt_amount,
                         trade_status, seller_status + '/' + buyer_status, buyer_tgid),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("已发货", callback_data=str('已发货')),
                         InlineKeyboardButton("取消并退款", callback_data=str('取消并退款'))],
                    ]
                    bot.send_message(
                        chat_id=user_id,
                        text='交易会在7天后自动收货,你也可以提醒买家提前收货\n'
                             '💎商品名：[{}](https://t.me/{}?start=goods{})\n'
                             '💎订单创建时间：{}\n'
                             '🔴结束时间：{}\n'
                             '💎价格：*{}* USDT\n'
                             '🔴状态：{}\n'
                             '🔴详细状态：{}\n'
                             '💎[联系买家](tg://user?id={}) (无法点击说明已销号)'.format
                        (goods_name, BOT_USERNAME, goods_uid, struct_time(creat_time),
                         struct_time(end_time), usdt_amount,
                         trade_status, seller_status + '/' + buyer_status, buyer_tgid),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown'
                    )
            elif trade_status == '交易完成':
                bot.send_message(
                    chat_id=user_id,
                    text='该交易已经完成！\n'
                         '💎商品名：[{}](https://t.me/{}?start=goods{})\n'
                         '💎订单创建时间：{}\n'
                         '🔴结束时间：{}\n'
                         '💎价格：*{}* USDT\n'
                         '🔴状态：{}\n'
                         '🔴详细状态：{}\n'
                         '💎[联系买家](tg://user?id={}) (无法点击说明已销号)'.format
                    (goods_name, BOT_USERNAME, goods_uid, struct_time(creat_time),
                     struct_time(end_time), usdt_amount,
                     trade_status, seller_status + '/' + buyer_status, buyer_tgid),
                    parse_mode='Markdown'
                )
        elif user_id == buyer_tgid:
            if trade_status == '交易完成':
                bot.send_message(
                    chat_id=user_id,
                    text='该交易已经完成！\n'
                         '💎商品名：[{}](https://t.me/{}?start=goods{})\n'
                         '💎订单创建时间：{}\n'
                         '🔴结束时间：{}\n'
                         '💎价格：*{}* USDT\n'
                         '🔴状态：{}\n'
                         '🔴详细状态：{}\n'
                         '💎[联系卖家](tg://user?id={}) (无法点击说明已销号)'.format
                    (goods_name, BOT_USERNAME, goods_uid, struct_time(creat_time),
                     struct_time(end_time), usdt_amount,
                     trade_status, buyer_status + '/' + seller_status, seller_tgid),
                    parse_mode='Markdown'
                )
            elif trade_status == '交易取消':
                bot.send_message(
                    chat_id=user_id,
                    text='该交易已经取消！款项已经退回到您的余额\n'
                         '💎商品名：[{}](https://t.me/{}?start=goods{})\n'
                         '💎订单创建时间：{}\n'
                         '🔴结束时间：{}\n'
                         '💎价格：*{}* USDT\n'
                         '🔴状态：{}\n'
                         '🔴详细状态：{}\n'
                         '💎[联系卖家](tg://user?id={}) (无法点击说明已销号)'.format
                    (goods_name, BOT_USERNAME, goods_uid, struct_time(creat_time),
                     struct_time(end_time), usdt_amount,
                     trade_status, buyer_status + '/' + seller_status, seller_tgid),
                    parse_mode='Markdown'
                )
            elif trade_status == '交易中':
                keyboard = [[
                    InlineKeyboardButton("确认收货", callback_data=str('确认收货')),
                    InlineKeyboardButton("申请退款", callback_data=str('申请退款'))],
                    [InlineKeyboardButton("延迟收货", callback_data=str('延迟收货'))]]
                bot.send_message(
                    chat_id=user_id,
                    text='该交易正在进行！如有️争议请保留证据截图联系客服\n'
                         '💎商品名：[{}](https://t.me/{}?start=goods{})\n'
                         '💎订单创建时间：{}\n'
                         '🔴结束时间：{}\n'
                         '💎价格：*{}* USDT\n'
                         '🔴状态：{}\n'
                         '🔴详细状态：{}\n'
                         '💎[联系卖家](tg://user?id={}) (无法点击说明已销号)'.format
                    (goods_name, BOT_USERNAME, goods_uid, struct_time(creat_time),
                     struct_time(end_time), usdt_amount,
                     trade_status, buyer_status + '/' + seller_status, seller_tgid),
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
    except Exception as e:
        print(e)


def already_deliver(update, context):
    user_id = update.effective_user.id
    print('进入 already_deliver 函数 | ' + str(user_id))
    trade_uid = context.user_data['trade_uid']
    trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
    goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
        trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
    seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
        trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
    if seller_tgid == user_id:
        if trade_status == '交易中':
            if seller_status == '待发货' or buyer_status == '申请退款':
                update_one_from_db('trade', 'seller_status', '已发货', 'uid', trade_uid)
                update_one_from_db('trade', 'buyer_status', '待收货', 'uid', trade_uid)
                bot.send_message(
                    chat_id=seller_tgid,
                    text='发货成功'
                )
                goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='您购买的{}，卖家已经发货，请确认后及时收货\n'
                         '自动收货时间：{}'.format(goods_name, struct_time(end_time)),
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(
                    chat_id=seller_tgid,
                    text='该交易已经发货或处于退款流程，无需发货！'
                )
        elif trade_status == '交易完成' or trade_status == '交易取消':
            bot.send_message(
                chat_id=seller_tgid,
                text='该交易已经完成或取消，无法再次发货！'
            )


def cancel_trade(update, context):
    user_id = update.effective_user.id
    print('进入 cancel_trade 函数 | ' + str(user_id))
    trade_uid = context.user_data['trade_uid']
    trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
    goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
        trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
    seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
        trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
    if seller_tgid == user_id:
        if trade_status == '交易取消' or trade_status == '交易完成':
            bot.send_message(
                chat_id=seller_tgid,
                text='订单已完成或已取消，无需再次操作！'
            )
        elif trade_status == '交易中':
            update_one_from_db('trade', 'trade_status', '交易取消', 'uid', trade_uid)
            update_one_from_db('user', 'frozen_balance', 0, 'tg_id', buyer_tgid)
            bot.send_message(
                chat_id=seller_tgid,
                text='订单已取消，已为买家退款'
            )
            goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
            buyer_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', buyer_tgid)
            now_balance = float(buyer_balance) + float(usdt_amount)
            update_one_from_db('user', 'available_balance', now_balance, 'tg_id', buyer_tgid)
            update_one_from_db('trade', 'seller_status', '已退款', 'uid', trade_uid)
            update_one_from_db('trade', 'trade_status', '交易取消', 'uid', trade_uid)
            bot.send_message(
                chat_id=buyer_tgid,
                text='您购买的产品{}，卖家已经取消订单，款项 *{}* USDT 已经退回到您的账户，请查收'.format(goods_name, usdt_amount),
                parse_mode='Markdown'
            )


def comfirm_goods(update, context):
    user_id = update.effective_user.id
    print('进入 comfirm_goods 函数 | ' + str(user_id))
    trade_uid = context.user_data['trade_uid']
    trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
    goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
        trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
    seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
        trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
    if user_id == buyer_tgid:
        if trade_status == '交易取消' or trade_status == '交易完成':
            bot.send_message(
                chat_id=buyer_tgid,
                text='订单已完成或已取消，无法再次操作！'
            )
        elif trade_status == '交易中':
            if seller_status == '待发货':
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='卖家还未发货，无法确认收货！'
                )
            else:
                now_time = get_now_time()
                update_one_from_db('trade', 'buyer_status', '已收货', 'uid', trade_uid)
                update_one_from_db('trade', 'seller_status', '已发货', 'uid', trade_uid)
                update_one_from_db('trade', 'trade_status', '交易完成', 'uid', trade_uid)
                update_one_from_db('trade', 'end_time', now_time, 'uid', trade_uid)
                seller_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', seller_tgid)
                now_balance = float(seller_balance) + float(usdt_amount)
                update_one_from_db('user', 'available_balance', now_balance, 'tg_id', seller_tgid)
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='交易完成，您已确认收货，款项已经打至卖家账户！'
                )
                bot.send_message(
                    chat_id=seller_tgid,
                    text='交易完成，买家确认收货，款项已经打至您账户！'
                )


def request_refund(update, context):
    user_id = update.effective_user.id
    print('进入 request_refund 函数 | ' + str(user_id))
    trade_uid = context.user_data['trade_uid']
    trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
    goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
        trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
    seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
        trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
    if user_id == buyer_tgid:
        if trade_status == '交易取消' or trade_status == '交易完成':
            bot.send_message(
                chat_id=buyer_tgid,
                text='订单已完成或已取消，无法再次操作！'
            )
        elif trade_status == '交易中':
            if buyer_status == '申请退款':
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='该交易已经是申请退款状态，无需再次申请，请等待卖家回应！'
                )
            else:
                update_one_from_db('trade', 'buyer_status', '申请退款', 'uid', trade_uid)
                now_time = get_now_time()
                two_day_later = int(now_time) + 172800
                update_one_from_db('trade', 'end_time', two_day_later, 'uid', trade_uid)
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='已向卖家申请退款，请等待[卖家](tg://user?id={})响应，或两天后自动退回你的账户。'.format(seller_tgid),
                    parse_mode='Markdown'
                )
                bot.send_message(
                    chat_id=seller_tgid,
                    text='[买家](tg://user?id={})提交了退款申请，前往[订单](https://t.me/{}?start=trade{})查看'.format
                    (buyer_tgid, BOT_USERNAME, trade_uid),
                    parse_mode='Markdown',
                )


def delay_time(update, context):
    try:
        user_id = update.effective_user.id
        print('进入 allow_refund 函数 | ' + str(user_id))
        trade_uid = context.user_data['trade_uid']
        trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
        goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
            trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
        seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
            trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
        goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
        if user_id == buyer_tgid:
            if trade_status == '交易取消' or trade_status == '交易完成':
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='订单已完成或已取消，无法再次操作！'
                )
            elif trade_status == '交易中' and buyer_status != '申请退款':
                if is_delayed == 'no':
                    end_time = creat_time + 1036800
                    update_one_from_db('trade', 'end_time', end_time, 'uid', trade_uid)
                    update_one_from_db('trade', 'is_delayed', 'yes', 'uid', trade_uid)
                    bot.send_message(
                        chat_id=buyer_tgid,
                        text='您已成功申请自动收货延期，已为您延长5天时间'
                    )
                    bot.send_message(
                        chat_id=seller_tgid,
                        text='[买家](tg://user?id={})购买的[{}](https://t.me/{}?start=goods{})已申请自动收货延期，已延长5天自动收货时间，'
                             '请与买家积极沟通并及时[发货](https://t.me/{}?start=trade{})'.format
                        (buyer_tgid, goods_name, BOT_USERNAME, goods_uid, BOT_USERNAME, trade_uid),
                        parse_mode='Markdown'
                    )
                elif is_delayed == 'yes':
                    bot.send_message(
                        chat_id=buyer_tgid,
                        text='您已经申请过延期，请勿再次申请，有问题请联系管理反馈！'
                    )
    except Exception as e:
        print(e)


def allow_refund(update, context):
    user_id = update.effective_user.id
    print('进入 allow_refund 函数 | ' + str(user_id))
    trade_uid = context.user_data['trade_uid']
    trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
    goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
        trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
    seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
        trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
    if user_id == seller_tgid:
        if trade_status == '交易取消' or trade_status == '交易完成':
            bot.send_message(
                chat_id=seller_tgid,
                text='订单已完成或已取消，无法再次操作！'
            )
        elif trade_status == '交易中':
            if buyer_status == '申请退款':
                buyer_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', buyer_tgid)
                now_balance = float(buyer_balance) + float(usdt_amount)
                update_one_from_db('user', 'available_balance', int(now_balance), 'tg_id', buyer_tgid)
                update_one_from_db('trade', 'seller_status', '已退款', 'uid', trade_uid)
                update_one_from_db('trade', 'trade_status', '交易取消', 'uid', trade_uid)
                update_one_from_db('user', 'frozen_balance', 0, 'tg_id', buyer_tgid)
                bot.send_message(
                    chat_id=buyer_tgid,
                    text='卖家已为您退款，款项已退回至您的账户，请查收！'
                )
                bot.send_message(
                    chat_id=seller_tgid,
                    text='退款成功，此交易已经取消！'
                )
            else:
                bot.send_message(
                    chat_id=seller_tgid,
                    text='订单不是申请退款状态，无法通过此操作发起退款！'
                )


def deny_refund(update, context):
    try:
        user_id = update.effective_user.id
        print('进入 deny_refund 函数 | ' + str(user_id))
        trade_uid = context.user_data['trade_uid']
        trade_infos = selectall_one_from_db('trade', 'uid', trade_uid)
        goods_uid, buyer_tgid, seller_tgid, price, buyer_status = \
            trade_infos[1], trade_infos[2], trade_infos[3], int(trade_infos[4]), trade_infos[5]
        seller_status, trade_status, creat_time, end_time, is_delayed, usdt_amount = \
            trade_infos[6], trade_infos[7], trade_infos[8], trade_infos[9], trade_infos[10], trade_infos[11]
        if user_id == seller_tgid:
            if trade_status == '交易取消' or trade_status == '交易完成':
                bot.send_message(
                    chat_id=seller_tgid,
                    text='订单已完成或已取消，无法再次操作！'
                )
            elif trade_status == '交易中':
                if buyer_status == '申请退款':
                    if seller_status == '拒绝退款':
                        bot.send_message(
                            chat_id=seller_tgid,
                            text='您已拒绝退款！无需再次操作'
                        )
                    else:
                        update_one_from_db('trade', 'seller_status', '拒绝退款', 'uid', trade_uid)
                        end_time = creat_time + 604800
                        update_one_from_db('trade', 'end_time', end_time, 'uid', trade_uid)
                        bot.send_message(
                            chat_id=buyer_tgid,
                            text='卖家拒绝退款，7天自动收货时间重新生效，如有异议，请联系客服反馈！'
                        )
                        bot.send_message(
                            chat_id=seller_tgid,
                            text='您已拒绝退款！7天自动收货时间重新生效。'
                        )
                else:
                    bot.send_message(
                        chat_id=seller_tgid,
                        text='订单不是申请退款状态，无法通过此操作发起退款！'
                    )
    except Exception as e:
        print(e)


comfirm_goods_handler = CallbackQueryHandler(comfirm_goods, pattern='^' + str('确认收货') + '$')
request_refund_handler = CallbackQueryHandler(request_refund, pattern='^' + str('申请退款') + '$')
delay_time_handler = CallbackQueryHandler(delay_time, pattern='^' + str('延迟收货') + '$')
allow_refund_handler = CallbackQueryHandler(allow_refund, pattern='^' + str('同意退款') + '$')
deny_refund_handler = CallbackQueryHandler(deny_refund, pattern='^' + str('拒绝退款') + '$')
already_deliver_handler = CallbackQueryHandler(already_deliver, pattern='^' + str('已发货') + '$')
cancel_trade_handler = CallbackQueryHandler(cancel_trade, pattern='^' + str('取消并退款') + '$')
