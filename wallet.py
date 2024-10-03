import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN, MASTER_WALLET_ADDRESS, TRONGRID_API_KEY, ADMIN_ID
from func import selectone_one_from_db, update_one_from_db, generate_usdt_wallet, get_now_time, get_random_num
from tronpy import Tron
from tronpy.keys import PrivateKey
import sqlite3

ROUTE, WALLET_FUNC = range(2)

# Initialize Tron client with default mainnet configuration
# 去掉 api_key 参数，使用 Tron 类的默认配置
client = Tron(network='mainnet')

bot = telegram.Bot(token=TOKEN)

keyboard = [
    [InlineKeyboardButton("充币", callback_data=str('充币')),
     InlineKeyboardButton("提币", callback_data=str('提币')),
     InlineKeyboardButton("转账", callback_data=str('转账'))],
]


def wallet_start(update, context):
    print('进入 wallet_start 函数')
    user_id = update.effective_user.id
    available_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', user_id)
    frozen_balance = selectone_one_from_db('frozen_balance', 'user', 'tg_id', user_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        '💰你的可用余额: *{}* USDT\n'
        '⛔冻结余额: *{}* USDT\n'
        '👉快速充币请点击 [充币] 或联系管理员。'.format(available_balance, frozen_balance),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return WALLET_FUNC


def wallet_cancel(update, context):
    print('进入 wallet_cancel')
    update.message.reply_text('期待再次见到你～')
    return ConversationHandler.END


def recharge(update, context):
    try:
        print('进入 recharge 函数')
        query = update.callback_query
        query.answer()
        user_id = update.effective_user.id
        wallet_status = selectone_one_from_db('wallet_status', 'user', 'tg_id', user_id)
        usdt_address = selectone_one_from_db('usdt_address', 'user', 'tg_id', user_id)

        if wallet_status == '激活':
            if usdt_address:
                # 如果用户已经有USDT地址，直接发送充币地址
                bot.send_message(
                    chat_id=user_id,
                    text=f'充值地址：`{usdt_address}`\n\n'
                         '⚠️请务必确认充值为USDT (TRC20)，否则资金将无法到账！\n'
                         '地址有效期无限，请确保地址无误。',
                    parse_mode='Markdown'
                )
            else:
                # 如果用户没有USDT地址，为其生成一个新的子地址
                new_address, new_key = generate_usdt_wallet()
                update_one_from_db('user', 'usdt_address', new_address, 'tg_id', user_id)
                update_one_from_db('user', 'usdt_key', new_key, 'tg_id', user_id)
                bot.send_message(
                    chat_id=user_id,
                    text=f'已为您生成新的USDT充值地址：\n'
                         f'充值地址：`{new_address}`\n\n'
                         '⚠️请务必确认充值为USDT (TRC20)，否则资金将无法到账！\n'
                         '地址有效期无限，请确保地址无误。',
                    parse_mode='Markdown'
                )
            return WALLET_FUNC
        else:
            bot.send_message(
                chat_id=user_id,
                text='您的钱包已被锁定，如为误封，请联系管理解封！',
            )
    except Exception as e:
        print(e)


def withdraw(update, context):
    print('进入 withdraw 函数')
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    wallet_status = selectone_one_from_db('wallet_status', 'user', 'tg_id', user_id)
    available_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', user_id)
    if wallet_status == '激活':
        bot.send_message(
            chat_id=user_id,
            text=f'当前可用余额为： *{available_balance}* USDT\n'
                 f'最小提现金额为：20 USDT\n\n'
                 '请回复以下格式进行提现：\n'
                 '⚠️格式：TX:收款地址,提币金额\n\n'
                 '例：TX:TP3t8KuG3D... 25.5\n',
            parse_mode='Markdown'
        )
        return WALLET_FUNC
    else:
        bot.send_message(
            chat_id=user_id,
            text='您的钱包已被锁定，如为误封，请联系管理解封！',
        )


def withdraw_exec(update, context):
    print('进入 withdraw_exec 函数')
    user_input = update.message.text
    user_id = update.effective_user.id
    try:
        method, address_amount = user_input.split(':')
        address, withdraw_amount = address_amount.split(',')
        withdraw_amount = float(withdraw_amount)

        # 提币操作验证
        if withdraw_amount < 20.0:
            bot.send_message(
                chat_id=user_id,
                text='提币金额必须大于20 USDT！',
            )
            return WALLET_FUNC

        available_balance = selectone_one_from_db('available_balance', 'user', 'tg_id', user_id)

        if withdraw_amount > available_balance:
            bot.send_message(
                chat_id=user_id,
                text='您的可用余额不足，请确认您输入的提币金额是否正确！',
            )
            return WALLET_FUNC
        else:
            # 扣除可用余额，更新到冻结余额，等待管理员审核
            new_available_balance = available_balance - withdraw_amount
            update_one_from_db('user', 'available_balance', new_available_balance, 'tg_id', user_id)
            update_one_from_db('user', 'frozen_balance', withdraw_amount, 'tg_id', user_id)
            invoice_id = get_random_num()
            conn = sqlite3.connect('data.sqlite3')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO invoice VALUES (?,?,?,?,?,?,?)",
                           (invoice_id, user_id, get_now_time(), '提币', withdraw_amount, '待处理', address))
            conn.commit()
            conn.close()

            keyboard = [[InlineKeyboardButton("提币成功", callback_data=str('提币成功'))]]
            for i in ADMIN_ID:
                bot.send_message(
                    chat_id=i,
                    text=f'用户提币申请：\n\n'
                         f'账单ID：{invoice_id}\n'
                         f'TG ID：[ID {user_id}](tg://user?id={user_id})\n'
                         f'提现总金额：{withdraw_amount} USDT\n'
                         f'提币地址：{address}',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            bot.send_message(
                chat_id=user_id,
                text=f'您的 *{withdraw_amount}* USDT 提币申请已经提交审核，请等待管理确认。',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
    except Exception as e:
        print(e)
        bot.send_message(
            chat_id=user_id,
            text='格式错误，请重新输入！',
        )
        return WALLET_FUNC


def transfer(update, context):
    print('进入 transfer 函数')
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    wallet_status = selectone_one_from_db('wallet_status', 'user', 'tg_id', user_id)
    if wallet_status == '激活':
        bot.send_message(
            chat_id=user_id,
            text='转账功能正在开发中，敬请期待！',
        )
        return WALLET_FUNC
    else:
        bot.send_message(
            chat_id=user_id,
            text='您的钱包已被锁定，如为误封，请联系管理解封！',
        )


wallet_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex('^' + '🏧充币/提币/转账' + '$'), wallet_start)],

    states={
        WALLET_FUNC: [
            MessageHandler(Filters.regex('^' + '🏧充币/提币/转账' + '$'), wallet_start),
            CallbackQueryHandler(recharge, pattern='^' + str('充币') + '$'),
            CallbackQueryHandler(withdraw, pattern='^' + str('提币') + '$'),
            CallbackQueryHandler(transfer, pattern='^' + str('转账') + '$'),
            MessageHandler(Filters.regex(r"^TX:.*\d"), withdraw_exec),
        ],
    },
    fallbacks=[CommandHandler('cancel', wallet_cancel)]
)
