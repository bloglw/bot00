import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
from config import TOKEN, BOT_USERNAME, ADMIN_ID
import sqlite3
from func import get_random_num, selectone_one_from_db, check_user_status, selectall_one_from_db, update_one_from_db
from func import get_now_time
import re

bot = telegram.Bot(token=TOKEN)


def goods_display(update, context):
    try:
        user_id = update.effective_user.id
        print('进入 goods_display 函数 | ' + str(user_id))
        text = update.message.text
        rst = re.search(r"/start\s(goods|shop|trade)(\d+)", text)
        goods_uid = rst.group(2)
        context.user_data['goods_uid'] = goods_uid
        goods_infos = selectall_one_from_db('goods', 'uid', goods_uid)
        seller_tgid, goods_name, goods_desc, goods_price, goods_status = \
            goods_infos[1], goods_infos[2], goods_infos[3], goods_infos[4], goods_infos[5]
        print(goods_status)
        shop_status = selectone_one_from_db('status', 'user', 'tg_id', seller_tgid)
        if int(seller_tgid) == int(user_id):
            if shop_status == '锁定':
                update.message.reply_text(
                    text='您的店铺已被管理员锁定，无法编辑商品状态',
                )
            else:
                if goods_status == '下架' or goods_status == '锁定':
                    update.message.reply_text(
                        text='该商品目前已下架或锁定，无法访问',
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("❌下架", callback_data=str('下架宝贝')),
                         InlineKeyboardButton("💎分享宝贝", callback_data=str('分享宝贝'))],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    update.message.reply_text(
                        text='💎商品名:{}\n'
                             '💎描述:{}\n'
                             '💎上架状态:{}中\n'
                             '💎价格: *{}* USDT'.format
                        (goods_name, goods_desc, goods_status, goods_price),
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
        else:
            if shop_status == '打烊' or shop_status == '锁定':
                update.message.reply_text(
                    text='该商店已打烊或被锁定',
                )
            else:
                if goods_status == '下架' or goods_status == '锁定':
                    update.message.reply_text(
                        text='该商品目前已下架或锁定，无法访问',
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("购买", callback_data=str('购买')),
                         InlineKeyboardButton("投诉", callback_data=str('投诉'))],
                        [InlineKeyboardButton("进店", callback_data=str('进店')),
                         InlineKeyboardButton("💎分享宝贝", callback_data=str('分享宝贝'))]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    update.message.reply_text(
                        text='‼️请注意保护个人隐私‼️\n'
                             '❗️不支持担保交易请点击投诉❗️\n'
                             '----------\n'
                             '💎商品名:{}\n'
                             '💎描述:{}\n'
                             '💎[联系卖家](tg://user?id={})\n'
                             '----------\n'
                             '价格: *{}* USDT'.format
                        (goods_name, goods_desc, seller_tgid, goods_price),
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
    except Exception as e:
        print(e)


def del_goods(update, context):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    print('进入 del_goods 函数 | ' + str(user_id))
    goods_uid = context.user_data['goods_uid']
    print(goods_uid)
    goods_infos = selectall_one_from_db('goods', 'uid', goods_uid)
    seller_tgid, goods_name, goods_desc, goods_price, goods_status = \
        goods_infos[1], goods_infos[2], goods_infos[3], goods_infos[4], goods_infos[5]
    if goods_status == '锁定':
        bot.send_message(
            chat_id=user_id,
            text='目前该商品已被管理员锁定，无法下架处理'
        )
    elif goods_status == '上架':
        update_one_from_db('goods', 'status', '下架', 'uid', goods_uid)
        bot.send_message(
            chat_id=user_id,
            text='下架成功'
        )


def share_goods(update, context):
    try:
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        print('进入 share_goods 函数 | ' + str(user_id))
        goods_uid = context.user_data['goods_uid']
        print(goods_uid)
        bot.send_message(
            chat_id=user_id,
            text='分享宝贝链接为: https://t.me/{}?start=goods{}\n'
                 '赶紧发给好友吧！'.format(BOT_USERNAME, goods_uid),
        )
    except Exception as e:
        print(e)


def add_goods(update, context):
    try:
        user_id = update.effective_user.id
        print('进入 add_goods 函数 | ' + str(user_id))
        user_text = update.message.text
        if check_user_status(user_id):
            reg = re.compile(r"^标题:(.+)\n描述:(.+)\n价格:(\d+)$")
            rst = reg.search(user_text)
            if rst is None:
                bot.send_message(
                    chat_id=user_id,
                    text='格式不符合要求，请检查后重新输入！',
                    parse_mode='Markdown'
                )
            else:
                subject, desc, price = rst.group(1), rst.group(2), rst.group(3)
                print(subject, desc, price)
                if len(subject) > 20 or len(desc) > 200:
                    bot.send_message(
                        chat_id=user_id,
                        text='长度不符合要求，请检查后重新输入！',
                        parse_mode='Markdown'
                    )
                elif '_' in user_text:
                    bot.send_message(
                        chat_id=user_id,
                        text='格式不符合要求，请不要包含\\_，请检查后重新输入！',
                        parse_mode='Markdown'
                    )
                elif '20字内' in subject or '200字内' in desc or int(price) < 10 or int(price) > 100000:
                    bot.send_message(
                        chat_id=user_id,
                        text='长度或价格不符合要求，请检查后重新输入！',
                        parse_mode='Markdown'
                    )
                else:
                    uid = get_random_num()
                    conn = sqlite3.connect('data.sqlite3')
                    cursor = conn.cursor()
                    usdt_amount = int(price)
                    cursor.execute("INSERT INTO goods VALUES (?,?,?,?,?,?)",
                                   (uid, user_id, subject, desc, usdt_amount, '上架'))
                    conn.commit()
                    conn.close()
                    bot.send_message(
                        chat_id=user_id,
                        text='商品添加完毕，直达链接：[{}](https://t.me/{}?start=goods{})\n'
                             '-------\n'
                             '请确保你的商品支持担保交易。'.format(subject, BOT_USERNAME, uid),
                        parse_mode='Markdown'
                    )
        else:
            bot.send_message(
                chat_id=user_id,
                text='您当前账户状态异常，请联系管理员',
                parse_mode='Markdown'
            )
    except Exception as e:
        print(e)


def buy_goods(update, context):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    print('进入 buy_goods 函数 | ' + str(user_id))
    goods_uid = context.user_data['goods_uid']
    goods_infos = selectall_one_from_db('goods', 'uid', goods_uid)
    seller_tgid, goods_name, goods_desc, goods_price, goods_status = \
        goods_infos[1], goods_infos[2], goods_infos[3], goods_infos[4], goods_infos[5]
    keyboard = [
        [InlineKeyboardButton("确认无误,购买", callback_data=str('确认购买'))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=user_id,
        text='‼️请注意保护个人隐私‼️\n'
             '❗️不支持担保交易请点击投诉❗️\n'
             '----------\n'
             '💎商品名:{}\n'
             '💎描述:{}\n'
             '----------\n'
             '价格: *{}* USDT'.format
        (goods_name, goods_desc, goods_price),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


def buy_goods_comfirm(update, context):
    try:
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        wallet_status = selectone_one_from_db('wallet_status', 'user', 'tg_id', user_id)
        if wallet_status == '激活':
            print('进入 buy_goods_comfirm 函数 | ' + str(user_id))
            goods_uid = context.user_data['goods_uid']
            goods_infos = selectall_one_from_db('goods', 'uid', goods_uid)
            seller_tgid, goods_name, goods_desc, goods_price, goods_status = \
                goods_infos[1], goods_infos[2], goods_infos[3], goods_infos[4], goods_infos[5]
            usdt_price_amount = goods_price
            buyer_available_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', user_id)
            if float(buyer_available_balance) < float(usdt_price_amount):
                bot.send_message(
                    chat_id=user_id,
                    text='您的余额不足，请充值后购买！'
                )
            else:
                new_balance = float(buyer_available_balance) - float(usdt_price_amount)
                update_one_from_db('user', 'available_balance', new_balance, 'tg_id', user_id)
                conn = sqlite3.connect('data.sqlite3')
                cursor = conn.cursor()
                now_time = get_now_time()
                end_time = now_time + 604800
                trade_id = get_random_num()
                cursor.execute("INSERT INTO trade VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                    trade_id, int(goods_uid), int(user_id), int(seller_tgid), int(goods_price),
                    '待发货', '待发货', '交易中', now_time, end_time, 'no', usdt_price_amount))
                conn.commit()
                conn.close()
                reply_keyboard = [
                    ['👤买家中心', '🤵卖家中心'],
                    ['🏧充币/提币/转账', '🙋🏻‍️联系客服']
                ]
                bot.send_message(
                    chat_id=user_id,
                    text='购买成功，请联系 [卖家](tg://user?id={}) 发货，购买记录可在 买家中心 - 我买到的 查看 \n'
                         '\t\t\t----注意⚠️必读----\n'
                         '请在【7天】内完成交易，否则将自动打款给卖家。如果卖家以各种借口拖延您可使用延长收货或退'
                         '款功能以保证资金安全，没有完成交易前请勿相信卖家点击确认收货，交易中出现问题请联系客服，您'
                         '的款项在确认收货后将随时可能被卖家提取，届时将无法保证您的权益'.format(seller_tgid),
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
                    parse_mode='Markdown'
                )
                keyboard = [
                    [InlineKeyboardButton("🆕发布商品", callback_data=str('🆕发布商品')),
                     InlineKeyboardButton("🧰我的货架", callback_data=str('🧰我的货架'))],
                    [InlineKeyboardButton("✅交易完成", callback_data=str('✅交易完成')),
                     InlineKeyboardButton("⚠️交易中", callback_data=str('⚠️交易中'))],
                    [InlineKeyboardButton("🏖闭店休息", callback_data=str('🏖闭店休息')),
                     InlineKeyboardButton("💵恢复营业", callback_data=str('💵恢复营业'))],
                    [InlineKeyboardButton("💎分享店铺", callback_data=str('💎分享店铺'))],
                ]
                bot.send_message(
                    chat_id=seller_tgid,
                    text='[买家](tg://user?id={}) 已购买 {}，请尽快与之联系并[发货](https://t.me/{}?start=trade{})'.format(
                        user_id, goods_name, BOT_USERNAME, trade_id
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        else:
            bot.send_message(
                chat_id=user_id,
                text='您的钱包已被锁定，如为误封，请联系管理解封！',
            )
    except Exception as e:
        print(e)


def go_shop(update, context):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    goods_uid = context.user_data['goods_uid']
    seller_id = selectone_one_from_db('user_tgid', 'goods', 'uid', goods_uid)
    conn = sqlite3.connect('data.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from goods where user_tgid=? and status=?", (seller_id, '上架'))
    all_goods = cursor.fetchall()
    conn.close()
    ret_text = ''
    for i in all_goods:
        ret_text += '📦 [{}](https://t.me/{}?start=goods{}) \t\t {} USDT\n'.format(i[2], BOT_USERNAME, i[0], i[4])
    query.edit_message_text(
        text='🌈[{}](tg://user?id={})的店铺: \n'.format(seller_id, seller_id) + ret_text[:-1],
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


def complain(update, context):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    goods_uid = context.user_data['goods_uid']
    goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
    seller_id = selectone_one_from_db('user_tgid', 'goods', 'uid', goods_uid)
    seller_uuid = selectone_one_from_db('uuid', 'user', 'tg_id', seller_id)
    reply_keyboard = [
        ['👤买家中心', '🤵卖家中心'],
        ['🏧充币/提币/转账', '🙋🏻‍️联系客服']
    ]
    bot.send_message(
        chat_id=user_id,
        text='投诉功能仅适用于卖家不通过担保交易的违禁行为\n'
             '卖家唯一ID：`{}`\n'
             '如果卖家要求私下付款请联系客服反馈相关截图证据。我们将在核实后处罚该违禁商家！'.format(seller_uuid),
        reply_markup=ReplyKeyboardMarkup(reply_keyboard),
        parse_mode='Markdown'
    )
    for i in ADMIN_ID:
        bot.send_message(
            chat_id=i,
            text='[买家](tg://user?id={})因为商品 [{}](https://t.me/{}?start=goods{}) 发起投诉，'
                 '联系[卖家](tg://user?id={})'.format(user_id, goods_name, BOT_USERNAME, goods_uid, seller_id),
            parse_mode='Markdown'
        )


add_goods_handler = MessageHandler(Filters.regex(r"^标题:.+\n描述:.+\n价格:\d+"), add_goods)
del_goods_handler = CallbackQueryHandler(del_goods, pattern='^' + str('下架宝贝') + '$')
share_goods_handler = CallbackQueryHandler(share_goods, pattern='^' + str('分享宝贝') + '$')
buy_goods_handler = CallbackQueryHandler(buy_goods, pattern='^' + str('购买') + '$')
buy_goods_comfirm_handler = CallbackQueryHandler(buy_goods_comfirm, pattern='^' + str('确认购买') + '$')
go_shop_handler = CallbackQueryHandler(go_shop, pattern='^' + str('进店') + '$')
complain_handler = CallbackQueryHandler(complain, pattern='^' + str('投诉') + '$')
