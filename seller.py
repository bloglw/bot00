import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN, BOT_USERNAME
import sqlite3
from func import selectone_one_from_db, check_user_status

ROUTE, SELLER_FUNC = range(2)

bot = telegram.Bot(token=TOKEN)

keyboard = [
    [InlineKeyboardButton("🆕发布商品", callback_data=str('🆕发布商品')),
     InlineKeyboardButton("🧰我的货架", callback_data=str('🧰我的货架'))],
    [InlineKeyboardButton("✅交易完成", callback_data=str('✅交易完成')),
     InlineKeyboardButton("⏸交易中", callback_data=str('⏸交易中'))],
    [InlineKeyboardButton("🏖闭店休息", callback_data=str('🏖闭店休息')),
     InlineKeyboardButton("💵恢复营业", callback_data=str('💵恢复营业'))],
    [InlineKeyboardButton("💎分享店铺", callback_data=str('💎分享店铺'))],
]


def seller_start(update, context):
    print('进入 seller_start 函数')
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_id = update.effective_user.id
    available_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', user_id)
    update.message.reply_text(
        '欢迎！你的可用余额: *{}* USDT\n\n'
        '如需临时下架全部商品请选择🏖闭店休息,恢复上架请选择💵恢复营业'.format(available_balance),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return SELLER_FUNC


def seller_cancel(update, context):
    print('进入 seller_cancel')
    update.message.reply_text('期待再次见到你～')
    return ConversationHandler.END


def add_goods(update, context):
    print('进入 add_goods')
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if check_user_status(user_id):
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text='请复制以下模板发送给机器人\n'
                 '标题、描述作为解决纠纷的重要依据\n'
                 '️请勿发布无法界定价值的商品\n'
                 '️请勿发布多个完全一样的商品\n'
                 '价格为USDT，客户下单时将直接使用 USDT 进行交易',
            reply_markup=reply_markup
        )
        bot.send_message(
            chat_id=chat_id,
            text='标题:商品名称 (20字内)\n'
                 '描述:商品描述 (200字内)\n'
                 '价格:20 (大于10 USDT，小于100000 USDT)'
        )
        return SELLER_FUNC
    else:
        bot.send_message(
            chat_id=chat_id,
            text='店铺已被锁定！'
        )


def my_goods(update, context):
    print('进入 my_goods')
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    conn = sqlite3.connect('data.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from goods where user_tgid=? and status=?", (user_id, '上架'))
    rst = cursor.fetchall()
    conn.close()
    print(rst)
    reply_markup = InlineKeyboardMarkup(keyboard)
    ret_text = ''
    for i in rst:
        ret_text += '📦 [{}](https://t.me/{}?start=goods{}) \t\t {} USDT\n'.format(i[2], BOT_USERNAME, i[0], i[4])
    query.edit_message_text(
        text='🌈出售中的商品:\n' + ret_text[:-1],  # 删除最后一个多余的换行符
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    return SELLER_FUNC


def transaction_complete(update, context):
    print('进入 transaction_complete')
    user_id = update.effective_user.id
    query = update.callback_query
    query.answer()
    conn = sqlite3.connect('data.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from trade where seller_tgid=? and trade_status=?", (user_id, '交易完成'))
    rst = cursor.fetchall()
    conn.close()
    print(rst)
    reply_markup = InlineKeyboardMarkup(keyboard)
    ret_text = ''
    for i in rst:
        goods_uid = i[1]
        goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
        ret_text += '[{}](https://t.me/{}?start=trade{})\n'.format(goods_name, BOT_USERNAME, i[0])
    query.edit_message_text(
        text='🌈交易完成的订单:\n' + ret_text[:-1],  # 删除最后一个多余的换行符
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return SELLER_FUNC


def in_transaction(update, context):
    try:
        print('进入 in_transaction 函数')
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from trade where seller_tgid=? and trade_status=?", (user_id, '交易中'))
        rst = cursor.fetchall()
        conn.close()
        print(rst)
        reply_markup = InlineKeyboardMarkup(keyboard)
        ret_text = ''
        for i in rst:
            trade_uid, goods_uid, usdt_amount, seller_status = i[0], i[1], i[4], i[6]
            goods_name = selectone_one_from_db('title', 'goods', 'uid', goods_uid)
            ret_text += '{} \t [{}](https://t.me/{}?start=trade{}) \t *{}* USDT\n' \
                .format(seller_status, goods_name, BOT_USERNAME, trade_uid, usdt_amount)
        query.edit_message_text(
            text='交易中:\n' + ret_text[:-1],  # 删除最后一个多余的换行符
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return SELLER_FUNC
    except Exception as e:
        print(e)


def shop_close(update, context):
    query = update.callback_query
    query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if check_user_status(user_id):
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update user set status=? where tg_id=?", ('打烊', user_id,))
        conn.commit()
        conn.close()
        bot.send_message(
            chat_id=chat_id,
            text='您关闭了店铺，别人将无法看到您的商品'
        )
        return SELLER_FUNC
    else:
        bot.send_message(
            chat_id=chat_id,
            text='店铺已被锁定！'
        )


def shop_open(update, context):
    query = update.callback_query
    query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if check_user_status(user_id):
        conn = sqlite3.connect('data.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update user set status=? where tg_id=?", ('开张', user_id,))
        conn.commit()
        conn.close()
        bot.send_message(
            chat_id=chat_id,
            text='您的店铺开张啦，别人可以购买到您的商品'
        )
        return SELLER_FUNC
    else:
        bot.send_message(
            chat_id=chat_id,
            text='店铺已被锁定！'
        )


def share_shop(update, context):
    query = update.callback_query
    query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if check_user_status(user_id):
        shop_address = selectone_one_from_db('shop_address', 'user', 'tg_id', user_id)
        bot.send_message(
            chat_id=chat_id,
            text='您的专属店铺分享链接为:\n'
                 'https://t.me/{}?start=shop{}\n'
                 '点击复制，赶紧发给小伙伴吧！'.format(BOT_USERNAME, shop_address),
        )
        return SELLER_FUNC
    else:
        bot.send_message(
            chat_id=chat_id,
            text='店铺已被锁定！'
        )


seller_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^' + '🤵卖家中心' + '$'), seller_start)],
        states={
            SELLER_FUNC: [
                MessageHandler(Filters.regex('^' + '🤵卖家中心' + '$'), seller_start),
                CallbackQueryHandler(add_goods, pattern='^' + str('🆕发布商品') + '$'),
                CallbackQueryHandler(my_goods, pattern='^' + str('🧰我的货架') + '$'),
                CallbackQueryHandler(transaction_complete, pattern='^' + str('✅交易完成') + '$'),
                CallbackQueryHandler(in_transaction, pattern='^' + str('⏸交易中') + '$'),
                CallbackQueryHandler(shop_close, pattern='^' + str('🏖闭店休息') + '$'),
                CallbackQueryHandler(shop_open, pattern='^' + str('💵恢复营业') + '$'),
                CallbackQueryHandler(share_shop, pattern='^' + str('💎分享店铺') + '$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', seller_cancel)]
    )
